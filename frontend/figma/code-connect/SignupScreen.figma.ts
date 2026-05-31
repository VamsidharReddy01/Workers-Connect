// url=TODO: paste the published Figma component URL for the register screen, including node-id.
// source=frontend/lib/screens/signup_screen.dart
// component=SignupScreen
import figma from 'figma'

const instance = figma.selectedInstance

const initialRole = instance.getEnum('Initial Role', {
  Customer: 'customer',
  Worker: 'worker',
})

export default {
  example: figma.code`SignupScreen(initialRole: '${initialRole}')`,
  imports: ["import 'package:frontend/screens/signup_screen.dart';"],
  id: 'signup-screen',
  metadata: { nestable: false, props: { initialRole } },
}
