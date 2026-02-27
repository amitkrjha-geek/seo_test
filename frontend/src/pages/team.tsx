import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { ProjectMember } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Users, UserPlus, Shield, PenTool, Eye, Crown } from 'lucide-react'

const roleConfig: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  admin: { label: 'Admin', icon: Crown, color: 'text-red-600' },
  strategist: { label: 'Strategist', icon: Shield, color: 'text-blue-600' },
  writer: { label: 'Writer', icon: PenTool, color: 'text-green-600' },
  client: { label: 'Client', icon: Eye, color: 'text-gray-600' },
}

export default function TeamPage() {
  const { currentProject } = useProject()
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [newUserId, setNewUserId] = useState('')
  const [newRole, setNewRole] = useState('writer')
  const [isAdding, setIsAdding] = useState(false)

  useEffect(() => {
    if (currentProject) loadMembers()
  }, [currentProject])

  async function loadMembers() {
    if (!currentProject) return
    try {
      const data = await api.getProjectMembers(currentProject.id)
      setMembers(data)
    } catch { /* ignore */ }
  }

  async function addMember() {
    if (!currentProject || !newUserId) return
    setIsAdding(true)
    try {
      await api.addProjectMember(currentProject.id, { user_id: newUserId, role: newRole })
      setNewUserId('')
      loadMembers()
    } catch { /* ignore */ }
    setIsAdding(false)
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to manage team</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Team</h1>
        <p className="text-muted-foreground">Manage team members for {currentProject.name}</p>
      </div>

      {/* Role Legend */}
      <div className="flex gap-4 flex-wrap">
        {Object.entries(roleConfig).map(([role, config]) => {
          const Icon = config.icon
          return (
            <div key={role} className="flex items-center gap-1.5 text-sm">
              <Icon className={`h-4 w-4 ${config.color}`} />
              <span className="font-medium">{config.label}</span>
              <span className="text-muted-foreground">
                {role === 'admin' && '- Full access'}
                {role === 'strategist' && '- Manage pipeline'}
                {role === 'writer' && '- Write & edit content'}
                {role === 'client' && '- Read-only access'}
              </span>
            </div>
          )
        })}
      </div>

      {/* Add Member */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UserPlus className="h-4 w-4" /> Add Team Member
          </CardTitle>
          <CardDescription>Add a user by their user ID</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="User ID"
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              className="flex-1"
            />
            <div className="flex gap-3">
              <select className="border rounded-md px-3 py-2 text-sm bg-background flex-1 sm:flex-none" value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                <option value="admin">Admin</option>
                <option value="strategist">Strategist</option>
                <option value="writer">Writer</option>
                <option value="client">Client</option>
              </select>
              <Button onClick={addMember} disabled={isAdding || !newUserId} className="flex-1 sm:flex-none">
                <UserPlus className="h-4 w-4 mr-2" /> Add
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Member List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4" /> Members ({members.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {members.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No team members added yet</p>
          ) : (
            <div className="space-y-3">
              {members.map((member) => {
                const config = roleConfig[member.role] || roleConfig.writer
                const Icon = config.icon
                return (
                  <div key={member.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-sm font-medium">
                        {(member.user_name || member.user_email || '?')[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{member.user_name || 'Unknown'}</p>
                        <p className="text-xs text-muted-foreground">{member.user_email}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="gap-1">
                      <Icon className={`h-3 w-3 ${config.color}`} />
                      {config.label}
                    </Badge>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
