from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import OrderStatus
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.order_repository import OrderItemRepository, OrderRepository


class InvoiceService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = InvoiceRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.order_item_repo = OrderItemRepository(session, organization_id, is_superuser)

    def _generate_invoice_number(self) -> str:
        return f"INV-{uuid4().hex[:10].upper()}"

    async def generate_invoice(self, order_id: str, created_by: str | None = None) -> Invoice:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        if order.status in (OrderStatus.draft, OrderStatus.cancelled):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invoice a draft or cancelled order.")

        existing = await self.repo.get_for_order(order_id)
        if existing:
            return existing

        invoice_number = self._generate_invoice_number()
        while await self.repo.get_by_number(invoice_number):
            invoice_number = self._generate_invoice_number()

        invoice = Invoice(
            order_id=order_id,
            invoice_number=invoice_number,
            status=InvoiceStatus.issued,
            currency=order.currency,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            shipping_amount=order.shipping_amount,
            total=order.total,
            amount_paid=order.amount_paid,
            amount_due=round(order.total - order.amount_paid, 2),
            issued_at=datetime.utcnow(),
        )
        return await self.repo.create(invoice)

    async def _get_or_404(self, invoice_id: str) -> Invoice:
        invoice = await self.repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
        return invoice

    async def get_invoice(self, invoice_id: str) -> Invoice | None:
        return await self.repo.get_by_id(invoice_id)

    async def get_invoice_for_order(self, order_id: str) -> Invoice | None:
        return await self.repo.get_for_order(order_id)

    async def list_invoices(
        self,
        status_filter: InvoiceStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        items = await self.repo.list(status_filter, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(status_filter, q)
        return items, total

    async def sync_with_order(self, invoice_id: str) -> Invoice:
        """Refreshes amount_paid/amount_due from the order's current payment
        state and flips status to paid once the balance clears."""
        invoice = await self._get_or_404(invoice_id)
        if invoice.status == InvoiceStatus.void:
            return invoice

        order = await self.order_repo.get_by_id(invoice.order_id)
        if order:
            invoice.amount_paid = order.amount_paid
            invoice.amount_due = round(order.total - order.amount_paid, 2)
            invoice.status = InvoiceStatus.paid if invoice.amount_due <= 0 else InvoiceStatus.issued
        return await self.repo.save(invoice)

    async def void_invoice(self, invoice_id: str, reason: str | None = None) -> Invoice:
        invoice = await self._get_or_404(invoice_id)
        if invoice.status == InvoiceStatus.void:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice is already void.")

        invoice.status = InvoiceStatus.void
        invoice.voided_at = datetime.utcnow()
        invoice.void_reason = reason
        return await self.repo.save(invoice)

    async def render_html(self, invoice_id: str) -> str:
        """Renders a print-ready HTML representation of the invoice.

        This is a placeholder for real PDF generation: no PDF-rendering
        library (e.g. weasyprint/reportlab) is currently installed in this
        project, so invoices are generated as HTML that the browser can
        print/save-as-PDF. Swap this for a real PDF pipeline (and archive
        the output via FileService/S3) once that dependency is added."""
        invoice = await self._get_or_404(invoice_id)
        order = await self.order_repo.get_by_id(invoice.order_id)
        items = await self.order_item_repo.list_for_order(invoice.order_id)

        rows = "".join(
            f"<tr><td>{item.product_name}</td><td>{item.sku}</td><td>{item.quantity}</td>"
            f"<td>{item.unit_price:.2f}</td><td>{item.total:.2f}</td></tr>"
            for item in items
        )
        billing_name = f"{order.billing_first_name or ''} {order.billing_last_name or ''}".strip() if order else ""
        billing_address = ", ".join(filter(None, [
            order.billing_line1 if order else None, order.billing_city if order else None,
            order.billing_state if order else None, order.billing_country if order else None,
        ]))

        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Invoice {invoice.invoice_number}</title>
<style>
body {{ font-family: sans-serif; padding: 32px; color: #1a1a1a; }}
h1 {{ font-size: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
.totals td {{ border: none; }}
.totals tr td:first-child {{ text-align: right; }}
</style></head>
<body>
<h1>Invoice {invoice.invoice_number}</h1>
<p>Status: {invoice.status.value} &middot; Currency: {invoice.currency}</p>
<p><strong>Bill to:</strong> {billing_name}<br>{billing_address}</p>
<table>
<thead><tr><th>Item</th><th>SKU</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<table class="totals">
<tr><td>Subtotal</td><td>{invoice.subtotal:.2f}</td></tr>
<tr><td>Discount</td><td>-{invoice.discount_amount:.2f}</td></tr>
<tr><td>Tax</td><td>{invoice.tax_amount:.2f}</td></tr>
<tr><td>Shipping</td><td>{invoice.shipping_amount:.2f}</td></tr>
<tr><td><strong>Total</strong></td><td><strong>{invoice.total:.2f}</strong></td></tr>
<tr><td>Amount paid</td><td>{invoice.amount_paid:.2f}</td></tr>
<tr><td>Amount due</td><td>{invoice.amount_due:.2f}</td></tr>
</table>
</body></html>"""
