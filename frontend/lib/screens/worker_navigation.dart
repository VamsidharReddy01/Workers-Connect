import 'package:flutter/material.dart';

import '../models/user_model.dart';
import '../utils/constants.dart';
import 'profile_screen.dart';
import 'worker_dashboard.dart';
import 'worker_jobs_screen.dart';

class WorkerNavigation extends StatefulWidget {
  final UserModel user;
  final int initialIndex;

  const WorkerNavigation({
    super.key,
    required this.user,
    this.initialIndex = 0,
  });

  @override
  State<WorkerNavigation> createState() => _WorkerNavigationState();
}

class _WorkerNavigationState extends State<WorkerNavigation> {
  late int _currentIndex;
  final _jobsKey = GlobalKey<WorkerJobsScreenState>();

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
  }

  void _selectTab(int index) {
    setState(() => _currentIndex = index);
    if (index == 1) {
      _jobsKey.currentState?.refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      WorkerDashboard(user: widget.user),
      WorkerJobsScreen(key: _jobsKey, user: widget.user),
      ProfileScreen(initialUser: widget.user),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: IndexedStack(index: _currentIndex, children: screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _selectTab,
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.lightPrimary,
        unselectedItemColor: const Color(0xFFA2A7B8),
        elevation: 0,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.work_outline_rounded),
            activeIcon: Icon(Icons.work_rounded),
            label: 'Jobs',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline_rounded),
            activeIcon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
