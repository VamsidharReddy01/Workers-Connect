import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../utils/constants.dart';
import 'bookings_screen.dart';
import 'customer_dashboard.dart';
import 'messages_screen.dart';
import 'profile_screen.dart';

class MainNavigation extends StatefulWidget {
  final UserModel user;
  final int initialIndex;

  const MainNavigation({super.key, required this.user, this.initialIndex = 0});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  late int _currentIndex;
  final _bookingsKey = GlobalKey<BookingsScreenState>();
  final _messagesKey = GlobalKey<MessagesScreenState>();

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
  }

  void switchToTab(int index) {
    setState(() => _currentIndex = index);
    _refreshTab(index);
  }

  void _refreshTab(int index) {
    if (index == 1) _bookingsKey.currentState?.refresh();
    if (index == 2) _messagesKey.currentState?.refresh();
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      CustomerDashboard(
        user: widget.user,
        onBookingCreated: () {
          switchToTab(1);
          _messagesKey.currentState?.refresh();
        },
      ),
      BookingsScreen(key: _bookingsKey, user: widget.user),
      MessagesScreen(key: _messagesKey, user: widget.user),
      ProfileScreen(initialUser: widget.user),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: IndexedStack(index: _currentIndex, children: screens),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          boxShadow: [
            BoxShadow(
              color: Color(0x0A000000),
              blurRadius: 10,
              offset: Offset(0, -5),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() => _currentIndex = index);
            _refreshTab(index);
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          selectedItemColor: AppColors.lightPrimary,
          unselectedItemColor: const Color(0xFFA2A7B8),
          selectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
          unselectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 12,
          ),
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined),
              activeIcon: Icon(Icons.home_rounded),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.calendar_month_outlined),
              activeIcon: Icon(Icons.calendar_month_rounded),
              label: 'Bookings',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.chat_bubble_outline_rounded),
              activeIcon: Icon(Icons.chat_bubble_rounded),
              label: 'Messages',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline_rounded),
              activeIcon: Icon(Icons.person_rounded),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }
}
