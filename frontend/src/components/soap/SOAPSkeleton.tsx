import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const SECTION_ACCENTS = [
  "border-l-violet-400",
  "border-l-sky-400",
  "border-l-amber-400",
  "border-l-emerald-400",
];

export function SOAPSkeleton() {
  return (
    <div className="grid gap-3" role="status" aria-busy="true" aria-label="Generating SOAP note">
      {SECTION_ACCENTS.map((accent, i) => (
        <Card key={i} className={`border-l-4 ${accent}`}>
          <CardHeader className="pb-3 pt-5 px-5">
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-lg" />
              <div className="space-y-1.5">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-2.5 w-36" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-5 space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-[90%]" />
            <Skeleton className="h-3 w-[75%]" />
            {i === 2 && <Skeleton className="h-3 w-[60%]" />}
          </CardContent>
        </Card>
      ))}
      <span className="sr-only">Generating SOAP note, please wait.</span>
    </div>
  );
}
