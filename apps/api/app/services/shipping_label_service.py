from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_label import ShippingLabel, ShippingLabelType
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentItemRepository, ShipmentRepository
from app.repositories.shipping_label_repository import ShippingLabelRepository
from app.repositories.warehouse_repository import WarehouseRepository

LABEL_STYLE = """
body { font-family: sans-serif; padding: 24px; color: #1a1a1a; }
.label { max-width: 420px; border: 2px solid #1a1a1a; padding: 16px; margin-bottom: 24px; page-break-after: always; }
.label:last-child { page-break-after: auto; }
h1 { font-size: 16px; margin: 0 0 8px; }
.tracking { font-size: 22px; font-weight: 700; letter-spacing: 2px; margin: 12px 0; }
.barcode-bars { height: 48px; background: repeating-linear-gradient(90deg, #000 0 2px, #fff 2px 4px); margin: 8px 0; }
.barcode-note { font-size: 10px; color: #888; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { text-align: left; padding: 4px; border-bottom: 1px solid #ddd; font-size: 12px; }
.section { margin-top: 10px; font-size: 13px; }
.section strong { display: block; font-size: 11px; text-transform: uppercase; color: #666; }
"""


class ShippingLabelService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShippingLabelRepository(session, organization_id, is_superuser)
        self.shipment_repo = ShipmentRepository(session, organization_id, is_superuser)
        self.shipment_item_repo = ShipmentItemRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.warehouse_repo = WarehouseRepository(session, organization_id, is_superuser)

    async def _get_shipment_or_404(self, shipment_id: str):
        shipment = await self.shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
        return shipment

    async def _record(self, shipment_id: str, label_type: ShippingLabelType, generated_by: str | None) -> ShippingLabel:
        record = ShippingLabel(shipment_id=shipment_id, label_type=label_type, format="html", generated_by=generated_by)
        return await self.repo.create(record)

    def _label_block(self, shipment, order, warehouse, items) -> str:
        item_rows = "".join(f"<tr><td>{item.product_name}</td><td>{item.sku}</td><td>{item.quantity}</td></tr>" for item in items)
        return f"""
<div class="label">
  <h1>{warehouse.name if warehouse else 'Warehouse'} &rarr; {order.shipping_first_name} {order.shipping_last_name}</h1>
  <div class="section"><strong>Ship to</strong>{order.shipping_line1}, {order.shipping_city}, {order.shipping_state or ''} {order.shipping_postal_code or ''}, {order.shipping_country}</div>
  <div class="section"><strong>From</strong>{warehouse.name if warehouse else '-'}, {warehouse.city if warehouse else ''}, {warehouse.country if warehouse else ''}</div>
  <div class="tracking">{shipment.tracking_number or 'PENDING'}</div>
  <div class="barcode-bars"></div>
  <p class="barcode-note">Visual placeholder only -- not a scannable barcode. Render a real Code128/QR client-side (this app already ships jsbarcode/qrcode) when displaying this label in-browser.</p>
  <div class="section"><strong>Shipment</strong>{shipment.shipment_number} &middot; {shipment.carrier_name or 'Unassigned carrier'} &middot; {'COD ' + str(shipment.cod_amount) if shipment.is_cod else 'Prepaid'}</div>
  <table><thead><tr><th>Item</th><th>SKU</th><th>Qty</th></tr></thead><tbody>{item_rows}</tbody></table>
</div>
"""

    async def render_label_html(self, shipment_id: str, generated_by: str | None = None) -> str:
        shipment = await self._get_shipment_or_404(shipment_id)
        order = await self.order_repo.get_by_id(shipment.order_id)
        warehouse = await self.warehouse_repo.get_by_id(shipment.warehouse_id)
        items = await self.shipment_item_repo.list_for_shipment(shipment_id)

        await self._record(shipment_id, ShippingLabelType.label, generated_by)
        body = self._label_block(shipment, order, warehouse, items)
        return f"<!doctype html><html><head><meta charset='utf-8'><title>Label {shipment.shipment_number}</title><style>{LABEL_STYLE}</style></head><body>{body}</body></html>"

    async def render_packing_slip_html(self, shipment_id: str, generated_by: str | None = None) -> str:
        shipment = await self._get_shipment_or_404(shipment_id)
        order = await self.order_repo.get_by_id(shipment.order_id)
        items = await self.shipment_item_repo.list_for_shipment(shipment_id)

        await self._record(shipment_id, ShippingLabelType.packing_slip, generated_by)
        item_rows = "".join(f"<tr><td>{item.product_name}</td><td>{item.sku}</td><td>{item.quantity}</td></tr>" for item in items)
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>Packing Slip {shipment.shipment_number}</title><style>{LABEL_STYLE}</style></head>
<body>
<div class="label" style="page-break-after:auto;">
  <h1>Packing Slip &mdash; {shipment.shipment_number}</h1>
  <div class="section"><strong>Order</strong>{order.order_number if order else ''}</div>
  <div class="section"><strong>Ship to</strong>{order.shipping_first_name} {order.shipping_last_name}, {order.shipping_line1}, {order.shipping_city}, {order.shipping_country}</div>
  {f'<div class="section"><strong>Gift note</strong>{order.gift_note}</div>' if order and order.gift_note else ''}
  <table><thead><tr><th>Item</th><th>SKU</th><th>Qty</th></tr></thead><tbody>{item_rows}</tbody></table>
</div>
</body></html>"""

    async def render_manifest_html(self, warehouse_id: str, shipment_ids: list[str], generated_by: str | None = None) -> str:
        warehouse = await self.warehouse_repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

        rows = []
        for shipment_id in shipment_ids:
            shipment = await self._get_shipment_or_404(shipment_id)
            order = await self.order_repo.get_by_id(shipment.order_id)
            await self._record(shipment_id, ShippingLabelType.manifest, generated_by)
            destination = f"{order.shipping_city}, {order.shipping_country}" if order else "-"
            rows.append(
                f"<tr><td>{shipment.shipment_number}</td><td>{shipment.tracking_number or '-'}</td>"
                f"<td>{shipment.carrier_name or '-'}</td><td>{destination}</td><td>{shipment.weight or '-'}</td></tr>"
            )

        return f"""<!doctype html><html><head><meta charset='utf-8'><title>Manifest - {warehouse.name}</title><style>{LABEL_STYLE}</style></head>
<body>
<div class="label" style="max-width:100%; page-break-after:auto;">
  <h1>Dispatch Manifest &mdash; {warehouse.name}</h1>
  <p class="section">{len(shipment_ids)} shipment(s)</p>
  <table><thead><tr><th>Shipment #</th><th>Tracking #</th><th>Carrier</th><th>Destination</th><th>Weight</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>
</div>
</body></html>"""

    async def render_bulk_labels_html(self, shipment_ids: list[str], generated_by: str | None = None) -> str:
        blocks = []
        style = LABEL_STYLE
        for shipment_id in shipment_ids:
            shipment = await self._get_shipment_or_404(shipment_id)
            order = await self.order_repo.get_by_id(shipment.order_id)
            warehouse = await self.warehouse_repo.get_by_id(shipment.warehouse_id)
            items = await self.shipment_item_repo.list_for_shipment(shipment_id)
            await self._record(shipment_id, ShippingLabelType.label, generated_by)
            blocks.append(self._label_block(shipment, order, warehouse, items))

        return f"<!doctype html><html><head><meta charset='utf-8'><title>Bulk Labels</title><style>{style}</style></head><body>{''.join(blocks)}</body></html>"

    async def get_history(self, shipment_id: str) -> list[ShippingLabel]:
        return await self.repo.list_for_shipment(shipment_id)
