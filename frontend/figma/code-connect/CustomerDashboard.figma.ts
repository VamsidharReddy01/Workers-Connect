// url=TODO: paste the published Figma component URL for the customer home/dashboard screen, including node-id.
// source=frontend/lib/screens/customer_dashboard.dart
// component=CustomerDashboard
import figma from 'figma'

const instance = figma.selectedInstance

const username = instance.getString('Username')
const email = instance.getString('Email')
const location = instance.getString('Location')

export default {
  example: figma.code`
    CustomerDashboard(
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
    "import 'package:frontend/screens/customer_dashboard.dart';",
  ],
  id: 'customer-dashboard',
  metadata: { nestable: false, props: { username, email, location } },
}
