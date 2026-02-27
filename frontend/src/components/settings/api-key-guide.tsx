import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { HelpCircle, ExternalLink } from 'lucide-react'

const API_GUIDES: Record<string, {
  title: string
  steps: string[]
  url: string
  freeTier: string
}> = {
  anthropic: {
    title: 'Anthropic (Claude) API Key',
    steps: [
      'Go to console.anthropic.com',
      'Sign in or create an account',
      'Navigate to Settings → API Keys',
      'Click "Create Key"',
      'Give it a name (e.g. "SEO Agency")',
      'Copy the key and paste it here',
    ],
    url: 'https://console.anthropic.com/settings/keys',
    freeTier: '$5 free credits on signup',
  },
  openai: {
    title: 'OpenAI (GPT) API Key',
    steps: [
      'Go to platform.openai.com',
      'Sign in or create an account',
      'Navigate to API Keys section',
      'Click "Create new secret key"',
      'Give it a name and copy the key',
      'Paste the key here',
    ],
    url: 'https://platform.openai.com/api-keys',
    freeTier: '$5 free credits on signup',
  },
  google_ai: {
    title: 'Google AI (Gemini) API Key',
    steps: [
      'Go to aistudio.google.com',
      'Sign in with your Google account',
      'Click "Get API Key" in the top menu',
      'Click "Create API key in new project"',
      'Copy the generated key',
      'Paste it here',
    ],
    url: 'https://aistudio.google.com/apikey',
    freeTier: 'Free tier: 15 RPM, 1M tokens/min',
  },
  serper: {
    title: 'Serper.dev API Key',
    steps: [
      'Go to serper.dev',
      'Click "Sign Up" and create a free account',
      'After signup, go to Dashboard',
      'Your API key is shown on the dashboard',
      'Copy the key and paste it here',
    ],
    url: 'https://serper.dev/dashboard',
    freeTier: '2,500 free searches on signup',
  },
  textrazor: {
    title: 'TextRazor API Key',
    steps: [
      'Go to textrazor.com',
      'Click "Get a Free API Key"',
      'Create an account with your email',
      'After verification, go to Dashboard',
      'Your API key is displayed there',
      'Copy and paste it here',
    ],
    url: 'https://www.textrazor.com/console',
    freeTier: '500 free requests per day',
  },
  google_nlp: {
    title: 'Google Cloud NLP API Key',
    steps: [
      'Go to console.cloud.google.com',
      'Create a new project (or select existing)',
      'Enable the Cloud Natural Language API',
      'Go to APIs & Services → Credentials',
      'Click "Create Credentials" → "API Key"',
      'Copy the key and paste it here',
    ],
    url: 'https://console.cloud.google.com/apis/library/language.googleapis.com',
    freeTier: '5,000 units per month free',
  },
  pagespeed: {
    title: 'PageSpeed Insights API Key',
    steps: [
      'Go to console.cloud.google.com',
      'Create a new project (or select existing)',
      'Enable the PageSpeed Insights API',
      'Go to APIs & Services → Credentials',
      'Click "Create Credentials" → "API Key"',
      'Copy the key and paste it here',
    ],
    url: 'https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com',
    freeTier: '25,000 requests per day free',
  },
}

export function ApiKeyGuide({ provider }: { provider: string }) {
  const guide = API_GUIDES[provider]
  if (!guide) return null

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0" title="How to get this API key">
          <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base">{guide.title}</DialogTitle>
          <DialogDescription>Follow these steps to get your API key</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 mt-2">
          <ol className="space-y-2">
            {guide.steps.map((step, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                  {i + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-xs font-medium">Free tier</p>
              <p className="text-xs text-muted-foreground">{guide.freeTier}</p>
            </div>
            <a
              href={guide.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
            >
              Open Console <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
