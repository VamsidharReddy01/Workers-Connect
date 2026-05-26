import 'package:flutter/material.dart';
import '../utils/constants.dart';

class RoleSelector extends StatelessWidget {
  final String selectedRole;
  final ValueChanged<String> onRoleChanged;

  const RoleSelector({
    super.key,
    required this.selectedRole,
    required this.onRoleChanged,
  });

  @override
  Widget build(BuildContext context) {
    final isWorker = selectedRole == 'worker';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            'Register As',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.2,
            ),
          ),
        ),
        Row(
          children: [
            // Customer Card
            Expanded(
              child: GestureDetector(
                onTap: () => onRoleChanged('customer'),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    color: !isWorker
                        ? AppColors.accentViolet.withOpacity(0.15)
                        : Colors.white.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: !isWorker
                          ? AppColors.accentViolet
                          : AppColors.cardBorder,
                      width: !isWorker ? 2.0 : 1.0,
                    ),
                    boxShadow: !isWorker
                        ? [
                            BoxShadow(
                              color: AppColors.accentViolet.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ]
                        : [],
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.person_outline,
                        color: !isWorker ? AppColors.accentBlue : AppColors.textHint,
                        size: 28,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Customer',
                        style: TextStyle(
                          color: !isWorker ? Colors.white : AppColors.textSecondary,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 16),
            // Worker Card
            Expanded(
              child: GestureDetector(
                onTap: () => onRoleChanged('worker'),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    color: isWorker
                        ? AppColors.accentViolet.withOpacity(0.15)
                        : Colors.white.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isWorker
                          ? AppColors.accentViolet
                          : AppColors.cardBorder,
                      width: isWorker ? 2.0 : 1.0,
                    ),
                    boxShadow: isWorker
                        ? [
                            BoxShadow(
                              color: AppColors.accentViolet.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ]
                        : [],
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.engineering_outlined,
                        color: isWorker ? AppColors.accentPink : AppColors.textHint,
                        size: 28,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Worker',
                        style: TextStyle(
                          color: isWorker ? Colors.white : AppColors.textSecondary,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}
