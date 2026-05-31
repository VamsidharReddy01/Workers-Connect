// url=TODO: paste the published Figma component URL for the tab shell/navigation screen, including node-id.
// source=frontend/lib/screens/main_navigation.dart
// component=MainNavigation
import figma from 'figma'

const instance = figma.selectedInstance

const username = instance.getString('Username')
const email = instance.getString('Email')
const location = instance.getString('Location')

export default {
  example: figma.code`
    MainNavigation(
      user: const UserModel(
        id: 1,
        username: '${username}',
        email: '${email}',
        role: 'customer',
        location: '${location}',
      ),
    )
  `,
  imports: [
    "import 'package:frontend/models/user_model.dart';",
    "import 'package:frontend/screens/main_navigation.dart';",
  ],
  id: 'main-navigation',
  metadata: { nestable: false, props: { username, email, location } },
}
