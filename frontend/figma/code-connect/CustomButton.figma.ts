// url=TODO: paste the published Figma component URL for CustomButton, including node-id.
// source=frontend/lib/widgets/custom_button.dart
// component=CustomButton
import figma from 'figma'

const instance = figma.selectedInstance

const text = instance.getString('Text')
const isLoading = instance.getBoolean('Loading')

export default {
  example: figma.code`
    CustomButton(
      text: '${text}',
      isLoading: ${isLoading},
      onPressed: () {},
    )
  `,
  imports: ["import 'package:frontend/widgets/custom_button.dart';"],
  id: 'custom-button',
  metadata: { nestable: true, props: { text, isLoading } },
}
