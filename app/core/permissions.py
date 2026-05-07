from dataclasses import dataclass
from enum import Enum
from typing import Set, Dict, List, Optional, FrozenSet


class Resource(str, Enum):
	CONTENT = 'content'
	ADMIN = 'admin'
	USERS = 'users'
	SESSIONS = 'sessions'
	AUTH = 'auth'
	HEALTH = 'health'
	ROLES = 'roles'
	PERMISSIONS = 'permissions'


class Action(str, Enum):
	CREATE = 'create'
	READ = 'read'
	UPDATE = 'update'
	DELETE = 'delete'

	READ_COMMON = 'read:common'
	READ_EXCLUSIVE = 'read:exclusive'
	
	BLOCK = 'block'
	UNBLOCK = 'unblock'
	ASSIGN_ROLE = 'assign_role'
	REMOVE_ROLE = 'remove_role'

	REVOKE = 'revoke'
	REVOKE_ALL = 'revoke:all'

	HEALTH_CHECK = 'health:check'
	METRICS = 'metrics'


class Permission(str, Enum):
	CONTENT_READ_COMMON = 'content:read:common'
	CONTENT_READ_ROLE1 = 'content:read:role1'
	CONTENT_READ_ROLE2 = 'content:read:role2'
	CONTENT_READ_ADMIN = 'content:read:admin'
	CONTENT_WRITE_COMMON = 'content:write:common'
	CONTENT_WRITE_ROLE1 = 'content:write:role1'
	CONTENT_WRITE_ROLE2 = 'content:write:role2'
	CONTENT_WRITE_ADMIN = 'content:write:admin'

	USERS_READ = 'users:read'
	USERS_CREATE = 'users:create'
	USERS_UPDATE = 'users:update'
	USERS_DELETE = 'users:delete'
	USERS_BLOCK = 'users:block'
	USERS_UNBLOCK = 'users:unblock'
	USERS_ASSIGN_ROLE = 'users:assign_role'
	USERS_REMOVE_ROLE = 'users:remove_role'

	SESSIONS_READ = 'session:read'
	SESSIONS_REVOKE_SELF = 'session:revoke:self'
	SESSIONS_REVOKE_OTHER = 'sessions:revoke:other'
	SESSIONS_REVOKE_ALL = 'sessions:revoke:all'

	ROLES_READ = 'roles:read'
	ROLES_CREATE = 'roles:create'
	ROLES_UPDATE = 'roles:update'
	ROLES_DELETE = 'roles:delete'
	ROLES_ASSIGN_PERMISSION = 'roles:assign_permission'
	ROLES_REMOVE_PERMISSION = 'roles:remove_permission'
	   
	PERMISSIONS_READ = 'permissions:read'
	PERMISSIONS_CREATE = 'permissions:create'
	PERMISSIONS_UPDATE = 'permissions:update'
	PERMISSIONS_DELETE = 'permissions:delete'
		
	ADMIN_ACCESS = 'admin:access'
	ADMIN_AUDIT_READ = 'admin:audit:read'
	SYSTEM_HEALTH_READ = 'system:health:read'
	SYSTEM_METRICS_READ = 'system:metrics:read'
	SYSTEM_CONFIG_READ = 'system:config:read'
	SYSTEM_CONFIG_UPDATE = 'system:config:update'
		
	SUPER_ADMIN = '*'

	@classmethod
	def all_permissions(cls) -> Set[str]:
		return {p.value for p in cls}

	@classmethod
	def get_permissions_by_resource(cls, resource: Resource) -> List[str]:
		return [p.value for p in cls if p.value.startswith(f'{resource.value}:') and p.value != cls.SUPER_ADMIN]

	@classmethod
	def get_by_action(cls, action: Action) -> List[str]:
		return [p.value for p in cls if p.value.endswith(f':{action.value}') and p.value != cls.SUPER_ADMIN]

	@classmethod
	def is_valid(cls, permission: str) -> bool:
		return permission in cls.all_permissions() or permission == cls.SUPER_ADMIN


@dataclass(frozen=True)
class PermissionMetadata:
	name: str
	resource: Resource
	action: Action
	description: str
	is_super: bool = False
	depends_on: FrozenSet[str] = frozenset()

	def to_dict(self) -> dict:
		return {
			'name': self.name, 
			'resource': self.resource,
			'action': self.action,
			'description': self.description,
			'is_super': self.is_super,
			'depends_on': self.depends_on
		}


PERMISSION_REGISTRY: Dict[str, PermissionMetadata] = {
    Permission.CONTENT_READ_COMMON: PermissionMetadata(
        name=Permission.CONTENT_READ_COMMON,
        resource=Resource.CONTENT,
        action=Action.READ_COMMON,
        description="Read common content accessible to all authenticated users"
    ),
    Permission.CONTENT_READ_ROLE1: PermissionMetadata(
        name=Permission.CONTENT_READ_ROLE1,
        resource=Resource.CONTENT,
        action=Action.READ_EXCLUSIVE,
        description="Read role1 exclusive content"
    ),
    Permission.CONTENT_READ_ROLE2: PermissionMetadata(
        name=Permission.CONTENT_READ_ROLE2,
        resource=Resource.CONTENT,
        action=Action.READ_EXCLUSIVE,
        description="Read role2 exclusive content"
    ),
    Permission.CONTENT_READ_ADMIN: PermissionMetadata(
        name=Permission.CONTENT_READ_ADMIN,
        resource=Resource.CONTENT,
        action=Action.READ_EXCLUSIVE,
        description="Read admin dashboard content",
        depends_on=frozenset([Permission.ADMIN_ACCESS])
    ),
    Permission.CONTENT_WRITE_COMMON: PermissionMetadata(
        name=Permission.CONTENT_WRITE_COMMON,
        resource=Resource.CONTENT,
        action=Action.UPDATE,
        description="Write/update common content",
        depends_on=frozenset([Permission.CONTENT_READ_COMMON])
    ),
    Permission.CONTENT_WRITE_ROLE1: PermissionMetadata(
        name=Permission.CONTENT_WRITE_ROLE1,
        resource=Resource.CONTENT,
        action=Action.UPDATE,
        description="Write/update role1 exclusive content",
        depends_on=frozenset([Permission.CONTENT_READ_ROLE1])
    ),
    Permission.CONTENT_WRITE_ROLE2: PermissionMetadata(
        name=Permission.CONTENT_WRITE_ROLE2,
        resource=Resource.CONTENT,
        action=Action.UPDATE,
        description="Write/update role2 exclusive content",
        depends_on=frozenset([Permission.CONTENT_READ_ROLE2])
    ),
    Permission.CONTENT_WRITE_ADMIN: PermissionMetadata(
        name=Permission.CONTENT_WRITE_ADMIN,
        resource=Resource.CONTENT,
        action=Action.UPDATE,
        description="Write/update admin content",
        depends_on=frozenset([Permission.CONTENT_READ_ADMIN, Permission.ADMIN_ACCESS])
    ),
    
    Permission.USERS_READ: PermissionMetadata(
        name=Permission.USERS_READ,
        resource=Resource.USERS,
        action=Action.READ,
        description="View list of users and their basic information"
    ),
    Permission.USERS_CREATE: PermissionMetadata(
        name=Permission.USERS_CREATE,
        resource=Resource.USERS,
        action=Action.CREATE,
        description="Create new user accounts"
    ),
    Permission.USERS_UPDATE: PermissionMetadata(
        name=Permission.USERS_UPDATE,
        resource=Resource.USERS,
        action=Action.UPDATE,
        description="Update user information (username, role, etc.)",
        depends_on=frozenset([Permission.USERS_READ])
    ),
    Permission.USERS_DELETE: PermissionMetadata(
        name=Permission.USERS_DELETE,
        resource=Resource.USERS,
        action=Action.DELETE,
        description="Delete user accounts (soft or hard delete)"
    ),
    Permission.USERS_BLOCK: PermissionMetadata(
        name=Permission.USERS_BLOCK,
        resource=Resource.USERS,
        action=Action.BLOCK,
        description="Block user accounts, preventing login"
    ),
    Permission.USERS_UNBLOCK: PermissionMetadata(
        name=Permission.USERS_UNBLOCK,
        resource=Resource.USERS,
        action=Action.UNBLOCK,
        description="Unblock previously blocked user accounts"
    ),
    Permission.USERS_ASSIGN_ROLE: PermissionMetadata(
        name=Permission.USERS_ASSIGN_ROLE,
        resource=Resource.USERS,
        action=Action.ASSIGN_ROLE,
        description="Assign roles to users",
        depends_on=frozenset([Permission.USERS_READ, Permission.ROLES_READ])
    ),
    Permission.USERS_REMOVE_ROLE: PermissionMetadata(
        name=Permission.USERS_REMOVE_ROLE,
        resource=Resource.USERS,
        action=Action.REMOVE_ROLE,
        description="Remove roles from users",
        depends_on=frozenset([Permission.USERS_READ, Permission.ROLES_READ])
    ),
    
    Permission.SESSIONS_READ: PermissionMetadata(
        name=Permission.SESSIONS_READ,
        resource=Resource.SESSIONS,
        action=Action.READ,
        description="View active sessions"
    ),
    Permission.SESSIONS_REVOKE_SELF: PermissionMetadata(
        name=Permission.SESSIONS_REVOKE_SELF,
        resource=Resource.SESSIONS,
        action=Action.REVOKE,
        description="Revoke own sessions (logout)"
    ),
    Permission.SESSIONS_REVOKE_OTHER: PermissionMetadata(
        name=Permission.SESSIONS_REVOKE_OTHER,
        resource=Resource.SESSIONS,
        action=Action.REVOKE,
        description="Revoke other users' sessions",
        depends_on=frozenset([Permission.SESSIONS_READ])
    ),
    Permission.SESSIONS_REVOKE_ALL: PermissionMetadata(
        name=Permission.SESSIONS_REVOKE_ALL,
        resource=Resource.SESSIONS,
        action=Action.REVOKE_ALL,
        description="Revoke all sessions for a user",
        depends_on=frozenset([Permission.SESSIONS_READ])
    ),
    
    Permission.ROLES_READ: PermissionMetadata(
        name=Permission.ROLES_READ,
        resource=Resource.ROLES,
        action=Action.READ,
        description="View roles and their permissions"
    ),
    Permission.ROLES_CREATE: PermissionMetadata(
        name=Permission.ROLES_CREATE,
        resource=Resource.ROLES,
        action=Action.CREATE,
        description="Create new roles",
        depends_on=frozenset([Permission.PERMISSIONS_READ])
    ),
    Permission.ROLES_UPDATE: PermissionMetadata(
        name=Permission.ROLES_UPDATE,
        resource=Resource.ROLES,
        action=Action.UPDATE,
        description="Update role information",
        depends_on=frozenset([Permission.ROLES_READ])
    ),
    Permission.ROLES_DELETE: PermissionMetadata(
        name=Permission.ROLES_DELETE,
        resource=Resource.ROLES,
        action=Action.DELETE,
        description="Delete roles",
        depends_on=frozenset([Permission.ROLES_READ])
    ),
    Permission.ROLES_ASSIGN_PERMISSION: PermissionMetadata(
        name=Permission.ROLES_ASSIGN_PERMISSION,
        resource=Resource.ROLES,
        action=Action.ASSIGN_ROLE,
        description="Assign permissions to roles",
        depends_on=frozenset([Permission.ROLES_READ, Permission.PERMISSIONS_READ])
    ),
    Permission.ROLES_REMOVE_PERMISSION: PermissionMetadata(
        name=Permission.ROLES_REMOVE_PERMISSION,
        resource=Resource.ROLES,
        action=Action.REMOVE_ROLE,
        description="Remove permissions from roles",
        depends_on=frozenset([Permission.ROLES_READ, Permission.PERMISSIONS_READ])
    ),
    
    Permission.PERMISSIONS_READ: PermissionMetadata(
        name=Permission.PERMISSIONS_READ,
        resource=Resource.PERMISSIONS,
        action=Action.READ,
        description="View available permissions"
    ),
    Permission.PERMISSIONS_CREATE: PermissionMetadata(
        name=Permission.PERMISSIONS_CREATE,
        resource=Resource.PERMISSIONS,
        action=Action.CREATE,
        description="Create new permission definitions",
        is_super=True
    ),
    Permission.PERMISSIONS_UPDATE: PermissionMetadata(
        name=Permission.PERMISSIONS_UPDATE,
        resource=Resource.PERMISSIONS,
        action=Action.UPDATE,
        description="Update permission metadata",
        is_super=True
    ),
    Permission.PERMISSIONS_DELETE: PermissionMetadata(
        name=Permission.PERMISSIONS_DELETE,
        resource=Resource.PERMISSIONS,
        action=Action.DELETE,
        description="Delete permission definitions",
        is_super=True
    ),
    
    Permission.ADMIN_ACCESS: PermissionMetadata(
        name=Permission.ADMIN_ACCESS,
        resource=Resource.ADMIN,
        action=Action.READ,
        description="Access admin panel and admin endpoints"
    ),
    Permission.ADMIN_AUDIT_READ: PermissionMetadata(
        name=Permission.ADMIN_AUDIT_READ,
        resource=Resource.ADMIN,
        action=Action.READ,
        description="Read audit logs",
        depends_on=frozenset([Permission.ADMIN_ACCESS])
    ),
    Permission.SYSTEM_HEALTH_READ: PermissionMetadata(
        name=Permission.SYSTEM_HEALTH_READ,
        resource=Resource.HEALTH,
        action=Action.HEALTH_CHECK,
        description="Read system health status"
    ),
    Permission.SYSTEM_METRICS_READ: PermissionMetadata(
        name=Permission.SYSTEM_METRICS_READ,
        resource=Resource.HEALTH,
        action=Action.METRICS,
        description="Read system metrics (Prometheus, etc.)",
        depends_on=frozenset([Permission.SYSTEM_HEALTH_READ])
    ),
    Permission.SYSTEM_CONFIG_READ: PermissionMetadata(
        name=Permission.SYSTEM_CONFIG_READ,
        resource=Resource.HEALTH,
        action=Action.READ,
        description="Read system configuration",
        is_super=True
    ),
    Permission.SYSTEM_CONFIG_UPDATE: PermissionMetadata(
        name=Permission.SYSTEM_CONFIG_UPDATE,
        resource=Resource.HEALTH,
        action=Action.UPDATE,
        description="Update system configuration",
        is_super=True
    ),
    
    Permission.SUPER_ADMIN: PermissionMetadata(
        name=Permission.SUPER_ADMIN,
        resource=Resource.ADMIN,
        action=Action.READ,
        description="Super administrator with all permissions",
        is_super=True
    ),
}


def get_permission_metadata(permission: str) -> Optional[PermissionMetadata]:
    return PERMISSION_REGISTRY.get(permission)


def get_permissions_by_resource(resource: Resource) -> List[PermissionMetadata]:
    return [
        meta for meta in PERMISSION_REGISTRY.values()
        if meta.resource == resource
    ]


def get_permissions_by_action(action: Action) -> List[PermissionMetadata]:
    return [
        meta for meta in PERMISSION_REGISTRY.values()
        if meta.action == action
    ]


def validate_permission_dependencies(permissions: Set[str]) -> bool:
    for perm in permissions:
        meta = get_permission_metadata(perm)
        if meta and meta.depends_on:
            if not meta.depends_on.issubset(permissions):
                return False
    return True


def expand_permissions_with_dependencies(permissions: Set[str]) -> Set[str]:
    expanded = set(permissions)
    changed = True
    
    while changed:
        changed = False
        for perm in list(expanded):
            meta = get_permission_metadata(perm)
            if meta and meta.depends_on:
                for dep in meta.depends_on:
                    if dep not in expanded:
                        expanded.add(dep)
                        changed = True
    
    return expanded


def get_default_permissions() -> Set[str]:
    return {
        Permission.CONTENT_READ_COMMON,
    }


def get_role_default_permissions() -> Dict[str, Set[str]]:
    return {
        "role1": {
            Permission.CONTENT_READ_COMMON,
            Permission.CONTENT_READ_ROLE1,
        },
        "role2": {
            Permission.CONTENT_READ_COMMON,
            Permission.CONTENT_READ_ROLE2,
        },
        "admin": expand_permissions_with_dependencies({
            Permission.ADMIN_ACCESS,
            Permission.USERS_READ,
            Permission.USERS_BLOCK,
            Permission.USERS_UNBLOCK,
            Permission.SESSIONS_READ,
            Permission.SESSIONS_REVOKE_OTHER,
            Permission.SESSIONS_REVOKE_ALL,
            Permission.ROLES_READ,
            Permission.PERMISSIONS_READ,
            Permission.SYSTEM_HEALTH_READ,
        }),
    }


def _validate_registry() -> None:
    missing = []
    for perm in Permission.all_permissions():
        if perm not in PERMISSION_REGISTRY:
            missing.append(perm)
    
    if missing:
        raise RuntimeError(
            f"Missing registry entries for permissions: {', '.join(missing)}"
        )
    
    for perm_name in PERMISSION_REGISTRY:
        if not Permission.is_valid(perm_name) and perm_name != Permission.SUPER_ADMIN:
            raise RuntimeError(
                f"Registry contains invalid permission name: {perm_name}"
            )



_validate_registry()
