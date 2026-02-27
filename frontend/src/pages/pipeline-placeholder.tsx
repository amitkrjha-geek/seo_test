import { useLocation } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PIPELINE_STEPS } from '@/lib/types'

const stepMap: Record<string, number> = {
  '/audit': 1,
  '/keywords': 2,
  '/competitors': 3,
  '/brief': 4,
  '/write': 5,
  '/optimize': 6,
  '/track': 7,
}

export default function PipelinePlaceholder() {
  const location = useLocation()
  const stepNum = stepMap[location.pathname] || 0
  const step = PIPELINE_STEPS.find((s) => s.step === stepNum)

  return (
    <div className="mx-auto max-w-2xl py-12">
      <Card>
        <CardHeader className="text-center">
          <Badge className="mx-auto mb-2 w-fit">Step {step?.step}</Badge>
          <CardTitle className="text-2xl">{step?.label}</CardTitle>
        </CardHeader>
        <CardContent className="text-center text-muted-foreground">
          <p>{step?.description}</p>
          <p className="mt-4 text-sm">This feature will be built in Phase {(step?.step || 0) <= 1 ? 2 : Math.min(Math.ceil((step?.step || 0) / 2) + 1, 5)}.</p>
        </CardContent>
      </Card>
    </div>
  )
}
