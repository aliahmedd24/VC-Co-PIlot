"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useSuccessStories } from "@/lib/hooks/useTools";
import { Star, ArrowRight, Minus } from "lucide-react";

export function SuccessStoryMatcher() {
  const [industry, setIndustry] = useState("");
  const [businessModel, setBusinessModel] = useState("");
  const mutation = useSuccessStories();

  const handleSubmit = () => {
    mutation.mutate({
      industry: industry || "saas",
      business_model: businessModel || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Industry</Label>
          <Input
            placeholder="saas, fintech, etc."
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Business Model</Label>
          <Input
            placeholder="subscription, marketplace, etc."
            value={businessModel}
            onChange={(e) => setBusinessModel(e.target.value)}
          />
        </div>
      </div>

      <Button onClick={handleSubmit} disabled={mutation.isPending}>
        {mutation.isPending ? "Matching..." : "Find Success Stories"}
      </Button>

      {mutation.data && (
        <div className="space-y-4">
          {mutation.data.matches.map((match) => (
            <Card key={match.name}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-yellow-500" />
                    {match.name}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{match.industry}</Badge>
                    <Badge variant="outline">
                      {(match.similarity_score * 100).toFixed(0)}% match
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Peak: {match.peak_valuation}
                    </span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  {match.parallels.length > 0 && (
                    <div>
                      <h4 className="mb-1 text-xs font-medium text-green-600 uppercase">
                        Parallels
                      </h4>
                      <ul className="space-y-1">
                        {match.parallels.map((p, i) => (
                          <li key={i} className="flex items-center gap-1 text-sm">
                            <ArrowRight className="h-3 w-3 text-green-500" />
                            {p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {match.differences.length > 0 && (
                    <div>
                      <h4 className="mb-1 text-xs font-medium text-muted-foreground uppercase">
                        Differences
                      </h4>
                      <ul className="space-y-1">
                        {match.differences.map((d, i) => (
                          <li key={i} className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Minus className="h-3 w-3" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
