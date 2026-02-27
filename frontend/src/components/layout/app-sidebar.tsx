import { Link, useLocation } from 'react-router-dom'
import {
  Search,
  FileText,
  BarChart3,
  Users,
  Settings,
  LayoutDashboard,
  Globe,
  Target,
  BookOpen,
  PenTool,
  Sparkles,
  TrendingUp,
  Compass,
  Newspaper,
  CalendarDays,
} from 'lucide-react'
import { useProject } from '@/hooks/use-project'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

const pipelineNav = [
  { label: 'Audit', href: '/audit', icon: Globe, step: 1 },
  { label: 'Keywords', href: '/keywords', icon: Search, step: 2 },
  { label: 'Competitors', href: '/competitors', icon: Target, step: 3 },
  { label: 'Brief', href: '/brief', icon: BookOpen, step: 4 },
  { label: 'Write', href: '/write', icon: PenTool, step: 5 },
  { label: 'Optimize', href: '/optimize', icon: Sparkles, step: 6 },
  { label: 'Track', href: '/track', icon: TrendingUp, step: 7 },
]

const mainNav = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
]

const strategyNav = [
  { label: 'Strategy', href: '/strategy', icon: Compass },
  { label: 'Past Articles', href: '/past-articles', icon: Newspaper },
  { label: 'Calendar', href: '/calendar', icon: CalendarDays },
]

const bottomNav = [
  { label: 'Content', href: '/content', icon: FileText },
  { label: 'Reports', href: '/reports', icon: BarChart3 },
  { label: 'Team', href: '/team', icon: Users },
  { label: 'Settings', href: '/settings', icon: Settings },
]

export function AppSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()
  const { currentProject } = useProject()

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
          S
        </div>
        <span className="font-semibold text-lg">SEO Agency</span>
      </div>

      {currentProject && (
        <div className="border-b px-4 py-3">
          <p className="text-xs text-muted-foreground">Current Project</p>
          <p className="font-medium text-sm truncate">{currentProject.name}</p>
          <p className="text-xs text-muted-foreground truncate">{currentProject.domain}</p>
        </div>
      )}

      <ScrollArea className="flex-1 px-3 py-2">
        <nav className="space-y-1">
          {mainNav.map((item) => (
            <SidebarLink key={item.href} item={item} isActive={location.pathname === item.href} onNavigate={onNavigate} />
          ))}
        </nav>

        <Separator className="my-3" />

        <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Pipeline
        </p>
        <nav className="space-y-1">
          {pipelineNav.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              isActive={location.pathname === item.href}
              step={item.step}
              onNavigate={onNavigate}
            />
          ))}
        </nav>

        <Separator className="my-3" />

        <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Strategy
        </p>
        <nav className="space-y-1">
          {strategyNav.map((item) => (
            <SidebarLink key={item.href} item={item} isActive={location.pathname === item.href} onNavigate={onNavigate} />
          ))}
        </nav>

        <Separator className="my-3" />

        <nav className="space-y-1">
          {bottomNav.map((item) => (
            <SidebarLink key={item.href} item={item} isActive={location.pathname === item.href} onNavigate={onNavigate} />
          ))}
        </nav>
      </ScrollArea>
    </aside>
  )
}

function SidebarLink({
  item,
  isActive,
  step,
  onNavigate,
}: {
  item: { label: string; href: string; icon: React.ComponentType<{ className?: string }> }
  isActive: boolean
  step?: number
  onNavigate?: () => void
}) {
  const Icon = item.icon
  return (
    <Link
      to={item.href}
      onClick={onNavigate}
      className={cn(
        'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
        isActive
          ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
      )}
    >
      {step !== undefined && (
        <span
          className={cn(
            'flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold',
            isActive ? 'bg-sidebar-primary text-sidebar-primary-foreground' : 'bg-muted text-muted-foreground'
          )}
        >
          {step}
        </span>
      )}
      {step === undefined && <Icon className="h-4 w-4" />}
      {item.label}
    </Link>
  )
}
