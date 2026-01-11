'use client';

/**
 * TemplatesLayer Component
 * Displays Golden Path Templates with ML Recommendations
 * Integrates with the ML Recommender API
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { FileCode, Sparkles, Star, Zap, Brain, RefreshCw, ChevronDown, TrendingUp } from 'lucide-react';
import { templatesApi } from '@/lib/api';
import { useGluePublish, useSelectedTemplate } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import type { Template, TemplateRecommendation, RecommendationResponse } from '@/types';

function TemplateTypeIcon({ type }: { type: Template['type'] }) {
  const icons = {
    api: <Zap className="h-4 w-4" />,
    batch: <FileCode className="h-4 w-4" />,
    stream: <Sparkles className="h-4 w-4" />,
    ml: <Brain className="h-4 w-4" />,
  };

  return icons[type] || <FileCode className="h-4 w-4" />;
}

function TemplateTypeBadge({ type }: { type: Template['type'] }) {
  const colors: Record<Template['type'], string> = {
    api: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    batch: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    stream: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    ml: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  };

  return (
    <Badge variant="outline" className={cn('uppercase text-xs', colors[type])}>
      {type}
    </Badge>
  );
}

function LanguageBadge({ language }: { language: Template['language'] }) {
  const colors: Record<Template['language'], string> = {
    python: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
    go: 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20',
    typescript: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  };

  return (
    <Badge variant="outline" className={cn('text-xs', colors[language])}>
      {language}
    </Badge>
  );
}

function PopularityStars({ popularity }: { popularity: number }) {
  const stars = Math.min(5, Math.max(0, Math.round(popularity / 20)));

  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={cn(
            'h-3 w-3',
            i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
          )}
        />
      ))}
    </div>
  );
}

function RecommendationScore({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  const getColor = () => {
    if (percentage >= 80) return 'text-green-500 bg-green-500/10';
    if (percentage >= 60) return 'text-yellow-500 bg-yellow-500/10';
    return 'text-orange-500 bg-orange-500/10';
  };

  return (
    <div className={cn('flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', getColor())}>
      <TrendingUp className="h-3 w-3" />
      {percentage}% match
    </div>
  );
}

interface TemplateCardProps {
  template: Template;
  isSelected: boolean;
  onSelect: () => void;
  recommendation?: TemplateRecommendation;
}

function TemplateCard({ template, isSelected, onSelect, recommendation }: TemplateCardProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isSelected && 'ring-2 ring-purple-500',
        recommendation && 'border-l-4 border-l-purple-500'
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <TemplateTypeIcon type={template.type} />
            <CardTitle className="text-base">{template.name}</CardTitle>
          </div>
          <TemplateTypeBadge type={template.type} />
        </div>
        {template.description && (
          <CardDescription className="line-clamp-2">
            {template.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <LanguageBadge language={template.language} />
          {recommendation ? (
            <RecommendationScore score={recommendation.score} />
          ) : (
            <PopularityStars popularity={template.popularity} />
          )}
        </div>
        {recommendation && (
          <p className="mt-2 text-xs text-muted-foreground italic">
            {recommendation.reason}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function TemplatesLoading() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {[...Array(6)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-5 w-32" />
            </div>
            <Skeleton className="h-4 w-full mt-2" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-3 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TemplatesEmpty() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <FileCode className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium">No templates found</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Golden Path templates will appear here
        </p>
      </div>
    </div>
  );
}

interface RecommenderFormProps {
  onRecommend: (workloadType: string, language: string) => void;
  isLoading: boolean;
}

function RecommenderForm({ onRecommend, isLoading }: RecommenderFormProps) {
  const [workloadType, setWorkloadType] = useState<string>('api');
  const [language, setLanguage] = useState<string>('typescript');
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-purple-500/5 to-blue-500/5">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <span className="font-medium">ML Recommender</span>
        </div>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="gap-1">
            {isOpen ? 'Hide' : 'Show'}
            <ChevronDown className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent>
        <div className="p-4 border-b bg-muted/30 space-y-4">
          <p className="text-sm text-muted-foreground">
            Get AI-powered template recommendations based on your workload requirements.
          </p>
          <div className="flex flex-wrap gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Workload Type</label>
              <Select value={workloadType} onValueChange={setWorkloadType}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="api">API Service</SelectItem>
                  <SelectItem value="batch">Batch Job</SelectItem>
                  <SelectItem value="stream">Stream Processing</SelectItem>
                  <SelectItem value="ml">ML Pipeline</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Language</label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="typescript">TypeScript</SelectItem>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="go">Go</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                onClick={() => onRecommend(workloadType, language)}
                disabled={isLoading}
                className="gap-2"
              >
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Get Recommendations
              </Button>
            </div>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function TemplatesLayer() {
  const publish = useGluePublish();
  const selectedTemplateId = useSelectedTemplate();
  const [recommendations, setRecommendations] = useState<TemplateRecommendation[] | null>(null);

  const { data: templates, isLoading, error } = useQuery({
    queryKey: ['templates'],
    queryFn: templatesApi.getAll,
  });

  const recommendMutation = useMutation({
    mutationFn: ({ workloadType, language }: { workloadType: string; language: string }) =>
      templatesApi.getRecommendations({
        workload_type: workloadType as 'api' | 'batch' | 'stream' | 'ml',
        language: language as 'python' | 'go' | 'typescript',
      }),
    onSuccess: (data: RecommendationResponse) => {
      setRecommendations(data.recommendations);
    },
  });

  const handleSelectTemplate = (template: Template) => {
    publish('template_id', template.id, 'templates');
  };

  const handleRecommend = (workloadType: string, language: string) => {
    recommendMutation.mutate({ workloadType, language });
  };

  if (isLoading) {
    return <TemplatesLoading />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center text-red-500">
          Failed to load templates: {(error as Error).message}
        </div>
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return <TemplatesEmpty />;
  }

  // If we have recommendations, show those first
  const recommendedTemplateIds = new Set(recommendations?.map((r) => r.template.id) || []);
  const recommendationMap = new Map(recommendations?.map((r) => [r.template.id, r]) || []);

  // Sort templates: recommended first (by score), then others by popularity
  const sortedTemplates = [...templates].sort((a, b) => {
    const aRec = recommendationMap.get(a.id);
    const bRec = recommendationMap.get(b.id);

    if (aRec && bRec) {
      return bRec.score - aRec.score;
    }
    if (aRec) return -1;
    if (bRec) return 1;
    return b.popularity - a.popularity;
  });

  // Group templates by type
  const templatesByType = templates.reduce((acc, template) => {
    if (!acc[template.type]) {
      acc[template.type] = [];
    }
    acc[template.type].push(template);
    return acc;
  }, {} as Record<string, Template[]>);

  return (
    <div>
      {/* ML Recommender Section */}
      <RecommenderForm onRecommend={handleRecommend} isLoading={recommendMutation.isPending} />

      <div className="p-4">
        {/* Stats Summary */}
        <div className="flex items-center gap-4 mb-4 text-sm">
          <span className="font-medium">{templates.length} templates</span>
          {recommendations && (
            <span className="text-purple-500 font-medium flex items-center gap-1">
              <Brain className="h-3 w-3" />
              {recommendations.length} recommended
            </span>
          )}
          {Object.entries(templatesByType).map(([type, items]) => (
            <span key={type} className="text-muted-foreground">
              {items.length} {type}
            </span>
          ))}
        </div>

        {/* Recommendations Section */}
        {recommendations && recommendations.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-purple-500 flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4" />
              AI Recommendations
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.map((rec) => (
                <TemplateCard
                  key={rec.template.id}
                  template={rec.template}
                  isSelected={selectedTemplateId === rec.template.id}
                  onSelect={() => handleSelectTemplate(rec.template)}
                  recommendation={rec}
                />
              ))}
            </div>
          </div>
        )}

        {/* All Templates Grid */}
        <div>
          {recommendations && recommendations.length > 0 && (
            <h3 className="text-sm font-medium text-muted-foreground mb-3">All Templates</h3>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedTemplates
              .filter((t) => !recommendedTemplateIds.has(t.id))
              .map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  isSelected={selectedTemplateId === template.id}
                  onSelect={() => handleSelectTemplate(template)}
                />
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TemplatesLayer;
