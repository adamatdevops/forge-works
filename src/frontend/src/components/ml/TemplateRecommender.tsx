'use client';

/**
 * Template Recommender Component
 * Allows users to input workload features and get ML-powered template recommendations
 */

import { useState } from 'react';
import { Cpu, Database, Loader2, Server, Sparkles, Zap } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { getRecommendation } from '@/lib/api/ml';
import type {
  DatabaseType,
  ProgrammingLanguage,
  RecommendationResponse,
  WorkloadFeatures,
  WorkloadType,
} from '@/types/ml';
import {
  DATABASE_LABELS,
  DEFAULT_WORKLOAD_FEATURES,
  LANGUAGE_LABELS,
  TEMPLATE_LABELS,
  WORKLOAD_LABELS,
} from '@/types/ml';

interface TemplateRecommenderProps {
  onSelect?: (templateId: string) => void;
}

export function TemplateRecommender({ onSelect }: TemplateRecommenderProps) {
  const [features, setFeatures] = useState<WorkloadFeatures>(DEFAULT_WORKLOAD_FEATURES);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await getRecommendation(features);
      setRecommendation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get recommendation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectTemplate = (templateId: string) => {
    onSelect?.(templateId);
  };

  const updateFeature = <K extends keyof WorkloadFeatures>(
    key: K,
    value: WorkloadFeatures[K]
  ) => {
    setFeatures((prev) => ({ ...prev, [key]: value }));
    // Clear previous recommendation when features change
    setRecommendation(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-amber-500" />
        <h3 className="text-lg font-semibold">Template Recommender</h3>
      </div>

      {/* Feature Input Form */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Language */}
        <div className="space-y-2">
          <Label htmlFor="language">Programming Language</Label>
          <Select
            value={features.language}
            onValueChange={(v) => updateFeature('language', v as ProgrammingLanguage)}
          >
            <SelectTrigger id="language">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(LANGUAGE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Workload Type */}
        <div className="space-y-2">
          <Label htmlFor="workload">Workload Type</Label>
          <Select
            value={features.workload_type}
            onValueChange={(v) => updateFeature('workload_type', v as WorkloadType)}
          >
            <SelectTrigger id="workload">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(WORKLOAD_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Database Type */}
        <div className="space-y-2">
          <Label htmlFor="database">Database</Label>
          <Select
            value={features.database_type}
            onValueChange={(v) => {
              updateFeature('database_type', v as DatabaseType);
              updateFeature('needs_database', v !== 'none');
            }}
          >
            <SelectTrigger id="database">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(DATABASE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Expected RPS */}
        <div className="space-y-2">
          <Label htmlFor="rps">Expected Requests/sec</Label>
          <Select
            value={String(features.expected_rps)}
            onValueChange={(v) => updateFeature('expected_rps', parseInt(v, 10))}
          >
            <SelectTrigger id="rps">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">Low (~10 RPS)</SelectItem>
              <SelectItem value="100">Medium (~100 RPS)</SelectItem>
              <SelectItem value="1000">High (~1K RPS)</SelectItem>
              <SelectItem value="10000">Very High (~10K RPS)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Boolean Options */}
      <div className="flex flex-wrap gap-3">
        <ToggleChip
          icon={<Database className="h-3.5 w-3.5" />}
          label="Queue"
          active={features.needs_queue}
          onClick={() => updateFeature('needs_queue', !features.needs_queue)}
        />
        <ToggleChip
          icon={<Zap className="h-3.5 w-3.5" />}
          label="Cache"
          active={features.needs_cache}
          onClick={() => updateFeature('needs_cache', !features.needs_cache)}
        />
        <ToggleChip
          icon={<Cpu className="h-3.5 w-3.5" />}
          label="GPU"
          active={features.needs_gpu}
          onClick={() => updateFeature('needs_gpu', !features.needs_gpu)}
        />
        <ToggleChip
          icon={<Server className="h-3.5 w-3.5" />}
          label="Compliance"
          active={features.compliance_required}
          onClick={() => updateFeature('compliance_required', !features.compliance_required)}
        />
      </div>

      {/* Submit Button */}
      <Button onClick={handleSubmit} disabled={isLoading} className="w-full">
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            Get Recommendation
          </>
        )}
      </Button>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Recommendation Results */}
      {recommendation && (
        <div className="space-y-4">
          {/* Primary Recommendation */}
          <div className="rounded-lg border-2 border-green-200 bg-green-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-green-600">
                  Recommended
                </div>
                <div className="text-lg font-semibold text-green-900">
                  {TEMPLATE_LABELS[recommendation.primary.template]}
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(recommendation.primary.confidence * 100)}%
                </div>
                <div className="text-xs text-green-600">confidence</div>
              </div>
            </div>
            <ul className="mt-3 space-y-1 text-sm text-green-700">
              {recommendation.primary.reasons.map((reason, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-green-500">✓</span>
                  {reason}
                </li>
              ))}
            </ul>
            <Button
              className="mt-4 w-full"
              onClick={() => handleSelectTemplate(recommendation.primary.template)}
            >
              Use This Template
            </Button>
          </div>

          {/* Alternative Recommendations */}
          {recommendation.alternatives.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">
                Alternatives
              </div>
              {recommendation.alternatives.map((alt) => (
                <div
                  key={alt.template}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-medium">{TEMPLATE_LABELS[alt.template]}</div>
                    <div className="text-xs text-muted-foreground">
                      {alt.reasons[0] || 'Alternative option'}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-muted-foreground">
                      {Math.round(alt.confidence * 100)}%
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSelectTemplate(alt.template)}
                    >
                      Select
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper component for toggle chips
interface ToggleChipProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

function ToggleChip({ icon, label, active, onClick }: ToggleChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-muted-foreground hover:bg-muted/80'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

export default TemplateRecommender;
