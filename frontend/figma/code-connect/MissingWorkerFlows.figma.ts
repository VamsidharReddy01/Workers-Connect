// url=TODO: paste a published Figma component URL for one of the not-yet-implemented worker flow pages.
// source=TODO: create Dart screens for worker search, worker detail, book service, booking details, wallet, and review.
// component=WorkersBridgeMissingFlow
import figma from 'figma'

const instance = figma.selectedInstance

const screen = instance.getEnum('Screen', {
  'Worker List': 'WorkerListScreen',
  'Worker Details': 'WorkerDetailsScreen',
  'Book Service': 'BookServiceScreen',
  'Booking Details': 'BookingDetailsScreen',
  Wallet: 'WalletScreen',
  'Rate Review': 'RateReviewScreen',
})

export default {
  example: figma.code`
    // TODO: Implement ${screen} in frontend/lib/screens, then replace this placeholder.
    const Placeholder()
  `,
  imports: ["import 'package:flutter/material.dart';"],
  id: 'workers-bridge-missing-flow',
  metadata: { nestable: false, props: { screen } },
}
