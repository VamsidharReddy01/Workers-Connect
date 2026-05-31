// url=TODO: paste the published Figma component URL for CustomTextField, including node-id.
// source=frontend/lib/widgets/custom_text_field.dart
// component=CustomTextField
import figma from 'figma'

const instance = figma.selectedInstance

const labelText = instance.getString('Label')
const hintText = instance.getString('Placeholder')
const isPassword = instance.getBoolean('Password')
const keyboardType = instance.getEnum('Keyboard Type', {
  Text: 'TextInputType.text',
  Email: 'TextInputType.emailAddress',
  Phone: 'TextInputType.phone',
  Number: 'TextInputType.number',
})

export default {
  example: figma.code`
    CustomTextField(
      controller: TextEditingController(),
      labelText: '${labelText}',
      hintText: '${hintText}',
      prefixIcon: Icons.text_fields,
      isPassword: ${isPassword},
      keyboardType: ${keyboardType},
    )
  `,
  imports: [
    "import 'package:flutter/material.dart';",
    "import 'package:frontend/widgets/custom_text_field.dart';",
  ],
  id: 'custom-text-field',
  metadata: { nestable: true, props: { labelText, hintText, isPassword, keyboardType } },
}
