export type UserRole = 'student' | 'teacher' | 'admin'

export interface UserProfile {
  id: string
  name: string
  role: UserRole
}
