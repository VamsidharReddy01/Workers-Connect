// url=TODO: paste the published Figma component URL for the worker dashboard screen, including node-id.
// source=frontend/lib/screens/worker_dashboard.dart
// component=WorkerDashboard
import figma from 'figma'

const instance = figma.selectedInstance

const username = instance.getString('Username')
const email = instance.getString('Email')
const location = instance.getString('Location')

export default {
  example: figma.code`
    WorkerDashboard(
      user: const UserModel(
        id: 2,
        username: '${username}',
        email: '${email}',
        role: 'worker',
        location: '${location}',
      ),
    )
  `,
  imports: [
    "import 'package:frontend/models/user_model.dart';",
    "import 'package:frontend/screens/worker_dashboard.dart';",
  ],
  id: 'worker-dashboard',
  metadata: { nestable: false, props: { username, email, location } },
}
