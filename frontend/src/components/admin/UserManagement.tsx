import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle, MoreHorizontal, Plus, ShieldCheck, UsersRound } from 'lucide-react';
import * as z from 'zod';
import { usersApi, type User } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const createSchema = z.object({
  email: z.string().email({ message: 'Enter a valid work email address.' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters.' }),
  role: z.enum(['admin', 'recruiter']),
});

type CreateValues = z.infer<typeof createSchema>;

export function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [userToDisable, setUserToDisable] = useState<User | null>(null);
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [updatingRoleId, setUpdatingRoleId] = useState<number | null>(null);
  const itemsPerPage = 10;

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { email: '', password: '', role: 'recruiter' },
  });

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * itemsPerPage;
      setUsers(await usersApi.getUsers(skip, itemsPerPage));
    } catch {
      setError('We could not load accounts. Check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const onSubmitCreate = async (data: CreateValues) => {
    setActionError(null);
    try {
      await usersApi.createUser(data);
      setIsCreateOpen(false);
      reset();
      await fetchUsers();
    } catch {
      setActionError('We could not create this account. Review the details and try again.');
    }
  };

  const onToggleStatus = async () => {
    if (!userToDisable) return;
    setActionError(null);
    setIsTogglingStatus(true);
    try {
      await usersApi.toggleUserActive(userToDisable.id);
      setUserToDisable(null);
      await fetchUsers();
    } catch {
      setActionError('We could not update account access. Please try again.');
    } finally {
      setIsTogglingStatus(false);
    }
  };

  const onUpdateRole = async (userId: number, newRole: 'admin' | 'recruiter') => {
    setActionError(null);
    setUpdatingRoleId(userId);
    try {
      await usersApi.updateUser(userId, { role: newRole });
      await fetchUsers();
    } catch {
      setActionError('We could not update the account role. Please try again.');
    } finally {
      setUpdatingRoleId(null);
    }
  };

  const firstVisibleUser = users.length === 0 ? 0 : (page - 1) * itemsPerPage + 1;
  const lastVisibleUser = (page - 1) * itemsPerPage + users.length;

  return (
    <div className="user-management">
      <section className="management-toolbar" aria-labelledby="users-heading">
        <div>
          <p className="page-label">Identity and access</p>
          <h1 id="users-heading">User management</h1>
          <p className="page-heading-copy">Control who can access recruitment operations and what they can manage.</p>
        </div>
        <div className="management-toolbar-actions">
          <span className="role-chip"><ShieldCheck size={14} aria-hidden="true" /> Admin workspace</span>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button><Plus aria-hidden="true" /> Add user</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[28rem]">
              <DialogHeader>
                <DialogTitle>Create account</DialogTitle>
                <DialogDescription>Give a recruiter or administrator access to this workspace.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit(onSubmitCreate)} className="space-y-4">
                <div className="form-field">
                  <Label htmlFor="create-email">Work email</Label>
                  <Input id="create-email" type="email" autoComplete="email" aria-invalid={Boolean(errors.email)} {...register('email')} />
                  {errors.email && <p className="form-error">{errors.email.message}</p>}
                </div>
                <div className="form-field">
                  <Label htmlFor="create-password">Temporary password</Label>
                  <Input id="create-password" type="password" autoComplete="new-password" aria-invalid={Boolean(errors.password)} {...register('password')} />
                  {errors.password && <p className="form-error">{errors.password.message}</p>}
                </div>
                <div className="form-field">
                  <Label htmlFor="create-role">Role</Label>
                  <Select defaultValue="recruiter" onValueChange={(value) => setValue('role', value as CreateValues['role'], { shouldValidate: true })}>
                    <SelectTrigger id="create-role"><SelectValue placeholder="Select a role" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="recruiter">Recruiter</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.role && <p className="form-error">{errors.role.message}</p>}
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting && <LoaderCircle className="animate-spin" aria-hidden="true" />}
                    {isSubmitting ? 'Creating account' : 'Create account'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </section>

      {error && (
        <Alert variant="destructive">
          <AlertDescription className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={() => void fetchUsers()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}
      {actionError && <Alert variant="destructive"><AlertDescription>{actionError}</AlertDescription></Alert>}

      <section aria-labelledby="account-table-heading">
        <div className="access-table-head">
          <div>
            <h2 id="account-table-heading">Accounts</h2>
            <p>Review active access and adjust roles when responsibilities change.</p>
          </div>
          <UsersRound aria-hidden="true" size={20} color="var(--primary)" />
        </div>
        <Card className="table-shell">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead><span className="sr-only">Actions</span></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? Array.from({ length: 5 }).map((_, index) => (
                    <TableRow key={`skeleton-${index}`} aria-busy="true">
                      <TableCell><div className="loading-bar w-48" /></TableCell>
                      <TableCell><div className="loading-bar w-20" /></TableCell>
                      <TableCell><div className="loading-bar w-16" /></TableCell>
                      <TableCell><div className="loading-bar w-24" /></TableCell>
                      <TableCell><div className="loading-bar ml-auto w-8" /></TableCell>
                    </TableRow>
                  )) : users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-44 text-center">
                        <UsersRound className="mx-auto mb-3 text-muted-foreground" aria-hidden="true" size={24} />
                        <p className="font-semibold text-foreground">No accounts found</p>
                        <p className="mt-1 text-sm text-muted-foreground">Add a new recruiter or administrator to get started.</p>
                      </TableCell>
                    </TableRow>
                  ) : users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="max-w-[17rem] truncate font-medium" title={user.email}>{user.email || '—'}</TableCell>
                      <TableCell><span className="role-chip">{user.role}</span></TableCell>
                      <TableCell>
                        <span className={`status-badge ${user.is_active ? 'status-badge--active' : 'status-badge--inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </TableCell>
                      <TableCell className="table-meta">{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</TableCell>
                      <TableCell className="user-actions-cell">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label={`Manage ${user.email}`}>
                              {updatingRoleId === user.id ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <MoreHorizontal aria-hidden="true" />}
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem disabled={updatingRoleId === user.id} onClick={() => void onUpdateRole(user.id, user.role === 'admin' ? 'recruiter' : 'admin')}>
                              Make {user.role === 'admin' ? 'recruiter' : 'administrator'}
                            </DropdownMenuItem>
                            <DropdownMenuItem className={user.is_active ? 'text-destructive focus:bg-destructive/10' : ''} onClick={() => setUserToDisable(user)}>
                              {user.is_active ? 'Disable account' : 'Enable account'}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {!isLoading && users.length > 0 && (
              <div className="table-pagination">
                <p className="table-pagination-copy">Showing {firstVisibleUser}–{lastVisibleUser} accounts</p>
                <div className="table-pagination-actions">
                  <Button variant="outline" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>Previous</Button>
                  <Button variant="outline" size="sm" onClick={() => setPage((current) => current + 1)} disabled={users.length < itemsPerPage}>Next</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <Dialog open={Boolean(userToDisable)} onOpenChange={(open) => !open && setUserToDisable(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{userToDisable?.is_active ? 'Disable account' : 'Enable account'}</DialogTitle>
            <DialogDescription>
              {userToDisable?.is_active
                ? 'Disable Account: Are you sure you want to disable this user account?'
                : 'Are you sure you want to enable this user account?'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserToDisable(null)} disabled={isTogglingStatus}>Cancel</Button>
            <Button variant={userToDisable?.is_active ? 'destructive' : 'default'} onClick={() => void onToggleStatus()} disabled={isTogglingStatus}>
              {isTogglingStatus && <LoaderCircle className="animate-spin" aria-hidden="true" />}
              {isTogglingStatus ? 'Updating access' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
