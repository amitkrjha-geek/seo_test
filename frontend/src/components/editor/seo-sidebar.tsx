import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'

interface SeoSidebarProps {
  text: string
  keyword: string
  seoScore: number | null
  metaTitle: string
  metaDescription: string
  onMetaTitleChange: (v: string) => void
  onMetaDescriptionChange: (v: string) => void
}

export function SeoSidebar({
  text,
  keyword,
  seoScore,
  metaTitle,
  metaDescription,
  onMetaTitleChange,
  onMetaDescriptionChange,
}: SeoSidebarProps) {
  const words = text.split(/\s+/).filter(Boolean)
  const wordCount = words.length
  const keywordLower = keyword.toLowerCase()
  const textLower = text.toLowerCase()

  // Calculate metrics
  const keywordCount = keywordLower ? (textLower.match(new RegExp(keywordLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')) || []).length : 0
  const density = wordCount > 0 ? ((keywordCount / wordCount) * 100).toFixed(1) : '0'
  const headingCount = (text.match(/^#{1,3}\s/gm) || []).length
  const paragraphCount = text.split(/\n\n+/).filter(p => p.trim() && !p.trim().startsWith('#')).length
  const keywordInFirst200 = keywordLower ? textLower.slice(0, 200).includes(keywordLower) : false

  const scoreColor = (seoScore ?? 0) >= 70 ? 'text-green-600' : (seoScore ?? 0) >= 40 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="space-y-3">
      {/* SEO Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">SEO Score</CardTitle>
        </CardHeader>
        <CardContent>
          {seoScore != null ? (
            <div className="text-center">
              <span className={`text-3xl font-bold ${scoreColor}`}>{seoScore}</span>
              <span className="text-muted-foreground text-sm">/100</span>
              <Progress value={seoScore} className="mt-2" />
            </div>
          ) : (
            <p className="text-xs text-muted-foreground text-center">Write content to see score</p>
          )}
        </CardContent>
      </Card>

      {/* Content Stats */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Content Stats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <StatRow label="Words" value={wordCount.toLocaleString()} good={wordCount >= 1000} />
          <StatRow label="Headings" value={headingCount.toString()} good={headingCount >= 3} />
          <StatRow label="Paragraphs" value={paragraphCount.toString()} good={paragraphCount >= 5} />
          {keyword && (
            <>
              <StatRow label="Keyword count" value={keywordCount.toString()} good={keywordCount >= 3} />
              <StatRow label="Keyword density" value={`${density}%`} good={parseFloat(density) >= 0.5 && parseFloat(density) <= 3} />
              <StatRow label="Keyword in intro" value={keywordInFirst200 ? 'Yes' : 'No'} good={keywordInFirst200} />
            </>
          )}
        </CardContent>
      </Card>

      {/* Meta */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Meta Tags</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs">Meta Title ({metaTitle.length}/60)</Label>
            <Input
              value={metaTitle}
              onChange={(e) => onMetaTitleChange(e.target.value)}
              placeholder="SEO page title..."
              className="text-xs h-8"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Meta Description ({metaDescription.length}/160)</Label>
            <textarea
              value={metaDescription}
              onChange={(e) => onMetaDescriptionChange(e.target.value)}
              placeholder="Page description for search results..."
              className="w-full rounded-md border px-3 py-2 text-xs min-h-[60px] resize-none bg-background"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function StatRow({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <Badge variant={good ? 'secondary' : 'outline'} className="text-[10px] px-1.5">
        {value}
      </Badge>
    </div>
  )
}
