import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/support_ticket_model.dart';
import '../services/auth_provider.dart';
import '../services/profile_service.dart';
import '../theme/light_form_theme.dart';
import '../utils/constants.dart';

class HelpSupportScreen extends StatefulWidget {
  const HelpSupportScreen({super.key});

  @override
  State<HelpSupportScreen> createState() => _HelpSupportScreenState();
}

class _HelpSupportScreenState extends State<HelpSupportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _subjectController = TextEditingController();
  final _messageController = TextEditingController();
  final _profileService = ProfileService();

  List<SupportTicketModel> _tickets = [];
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      Provider.of<AuthProvider>(context, listen: false).refreshUserProfile();
    });
    _loadTickets();
  }

  @override
  void dispose() {
    _subjectController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _loadTickets() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final tickets = await _profileService.getSupportTickets();
    if (!mounted) return;
    setState(() {
      _tickets = tickets;
      _isLoading = false;
      _error = tickets.isEmpty ? _profileService.lastErrorMessage : null;
    });
  }

  Future<void> _submitTicket() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isSubmitting = true;
      _error = null;
    });
    final ticket = await _profileService.submitTicket(
      subject: _subjectController.text,
      message: _messageController.text,
    );
    if (!mounted) return;
    setState(() => _isSubmitting = false);

    if (ticket == null) {
      setState(() {
        _error = _profileService.lastErrorMessage ?? 'Could not submit ticket.';
      });
      return;
    }

    _subjectController.clear();
    _messageController.clear();
    await Provider.of<AuthProvider>(
      context,
      listen: false,
    ).refreshUserProfile();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Support ticket submitted.'),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
    await _loadTickets();
  }

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: LightFormTheme.of(context),
      child: Scaffold(
        backgroundColor: const Color(0xFFF8FAFC),
        appBar: AppBar(
          backgroundColor: Colors.white,
          foregroundColor: const Color(0xFF1E212D),
          elevation: 0,
          scrolledUnderElevation: 0,
          title: const Text(
            'Help & Support',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(1),
            child: Container(color: const Color(0xFFE2E6F2), height: 1),
          ),
        ),
        body: RefreshIndicator(
          onRefresh: _loadTickets,
          color: AppColors.lightPrimary,
          child: ListView(
            padding: const EdgeInsets.all(20),
            physics: const AlwaysScrollableScrollPhysics(
              parent: BouncingScrollPhysics(),
            ),
            children: [
              _buildSubmitForm(),
              const SizedBox(height: 24),
              const Text(
                'Ticket History',
                style: TextStyle(
                  color: Color(0xFF1E212D),
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.all(28),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_error != null && _tickets.isEmpty)
                Text(_error!, style: const TextStyle(color: AppColors.error))
              else if (_tickets.isEmpty)
                const Text(
                  'No support tickets yet.',
                  style: TextStyle(color: Color(0xFF6E7489)),
                )
              else
                ..._tickets.map(_buildTicketCard),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSubmitForm() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E6F2)),
      ),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Submit a Ticket',
              style: TextStyle(
                color: Color(0xFF1E212D),
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _subjectController,
              validator: (value) {
                if (value == null || value.trim().length < 3) {
                  return 'Subject must be at least 3 characters';
                }
                return null;
              },
              decoration: _inputDecoration('Subject', Icons.subject_outlined),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _messageController,
              minLines: 4,
              maxLines: 6,
              validator: (value) {
                if (value == null || value.trim().length < 10) {
                  return 'Message must be at least 10 characters';
                }
                return null;
              },
              decoration: _inputDecoration('Message', Icons.message_outlined),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 48,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submitTicket,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.lightPrimary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: _isSubmitting
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text(
                        'Submit Ticket',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: const Color(0xFFA2A7B8)),
      filled: true,
      fillColor: const Color(0xFFF8FAFC),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Color(0xFFE2E6F2)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Color(0xFFE2E6F2)),
      ),
    );
  }

  Widget _buildTicketCard(SupportTicketModel ticket) {
    final color = switch (ticket.status) {
      'resolved' || 'closed' => AppColors.success,
      'in_progress' => AppColors.lightPrimary,
      _ => AppColors.warning,
    };

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E6F2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  ticket.subject,
                  style: const TextStyle(
                    color: Color(0xFF1E212D),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  ticket.statusDisplay,
                  style: TextStyle(
                    color: color,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            ticket.message,
            style: const TextStyle(color: Color(0xFF6E7489), height: 1.35),
          ),
          if (ticket.adminNote.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(
              'Admin: ${ticket.adminNote}',
              style: const TextStyle(
                color: Color(0xFF1E212D),
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
          const SizedBox(height: 10),
          Text(
            _formatDate(ticket.createdAt),
            style: const TextStyle(color: Color(0xFFA2A7B8), fontSize: 12),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }
}
