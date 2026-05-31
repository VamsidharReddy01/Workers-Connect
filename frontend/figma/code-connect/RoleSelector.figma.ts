// url=TODO: paste the published Figma component URL for RoleSelector, including node-id.
// source=frontend/lib/widgets/role_selector.dart
// component=RoleSelector
import figma from 'figma'

const instance = figma.selectedInstance

const selectedRole = instance.getEnum('Selected Role', {
  Customer: 'customer',
  Worker: 'worker',
})

export default {
  example: figma.code`
    RoleSelector(
      selectedRole: '${selectedRole}',
      onRoleChanged: (role) {},
    )
  `,
  imports: ["import 'package:frontend/widgets/role_selector.dart';"],
  id: 'role-selector',
  metadata: { nestable: true, props: { selectedRole } },
}
