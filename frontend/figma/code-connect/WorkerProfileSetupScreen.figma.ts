// url=TODO: paste the published Figma component URL for worker profile setup, including node-id.
// source=frontend/lib/screens/worker_profile_setup_screen.dart
// component=WorkerProfileSetupScreen
import figma from 'figma'

const instance = figma.selectedInstance

const username = instance.getString('Username')
const email = instance.getString('Email')

export default {
  example: figma.code`
    WorkerProfileSetupScreen(
      user: const UserModel(
        id: 2,
        username: '${username}',
        email: '${email}',
        role: 'worker',
      ),
    )
  `,
  imports: [
    "import 'package:frontend/models/user_model.dart';",
    "import 'package:frontend/screens/worker_profile_setup_screen.dart';",
  ],
  id: 'worker-profile-setup-screen',
  metadata: { nestable: false, props: { username, email } },
}
