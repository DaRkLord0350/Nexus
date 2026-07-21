import { SkeletonGrid, SkeletonRows } from '@/components/ui/skeleton';

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      <SkeletonGrid />
      <SkeletonRows count={3} />
    </div>
  );
}
