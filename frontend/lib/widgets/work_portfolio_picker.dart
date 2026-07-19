import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/worker_work_image_model.dart';
import '../utils/constants.dart';

class WorkPortfolioPicker extends StatelessWidget {
  final List<WorkerWorkImageModel> existingImages;
  final List<PortfolioLocalImage> pendingImages;
  final Set<int> removedExistingIds;
  final VoidCallback onPickImages;
  final void Function(int existingId) onRemoveExisting;
  final void Function(int pendingIndex) onRemovePending;
  final int maxImages;

  const WorkPortfolioPicker({
    super.key,
    required this.existingImages,
    required this.pendingImages,
    required this.removedExistingIds,
    required this.onPickImages,
    required this.onRemoveExisting,
    required this.onRemovePending,
    this.maxImages = 8,
  });

  int get _visibleExistingCount => existingImages
      .where((img) => !removedExistingIds.contains(img.id))
      .length;

  int get _totalCount => _visibleExistingCount + pendingImages.length;

  @override
  Widget build(BuildContext context) {
    final canAddMore = _totalCount < maxImages;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Work Portfolio Photos',
              style: TextStyle(
                color: Color(0xFF1E212D),
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              '$_totalCount / $maxImages',
              style: const TextStyle(
                color: Color(0xFF6E7489),
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        const Text(
          'Add photos of your completed work so customers can see your quality.',
          style: TextStyle(color: Color(0xFF6E7489), fontSize: 13, height: 1.4),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            ...existingImages
                .where((img) => !removedExistingIds.contains(img.id))
                .map(
                  (img) => _ImageTile(
                    imageProvider: NetworkImage(
                      ApiConstants.resolveMediaUrl(img.imageUrl),
                    ),
                    onRemove: () => onRemoveExisting(img.id),
                  ),
                ),
            ...List.generate(pendingImages.length, (index) {
              final pending = pendingImages[index];
              return _ImageTile(
                imageProvider: MemoryImage(pending.bytes),
                onRemove: () => onRemovePending(index),
              );
            }),
            if (canAddMore) _AddTile(onTap: onPickImages),
          ],
        ),
      ],
    );
  }
}

class PortfolioLocalImage {
  final String filename;
  final Uint8List bytes;

  const PortfolioLocalImage({required this.filename, required this.bytes});

  static Future<PortfolioLocalImage?> fromXFile(XFile file) async {
    final bytes = await file.readAsBytes();
    return PortfolioLocalImage(
      filename: file.name.isNotEmpty ? file.name : 'portfolio.jpg',
      bytes: bytes,
    );
  }
}

class _ImageTile extends StatelessWidget {
  final ImageProvider imageProvider;
  final VoidCallback onRemove;

  const _ImageTile({required this.imageProvider, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: Container(
            width: 92,
            height: 92,
            color: const Color(0xFFF1F3F8),
            child: Image(
              image: imageProvider,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Icon(
                Icons.broken_image_outlined,
                color: Color(0xFFA2A7B8),
              ),
            ),
          ),
        ),
        Positioned(
          top: -6,
          right: -6,
          child: Material(
            color: Colors.white,
            shape: const CircleBorder(),
            elevation: 2,
            child: InkWell(
              onTap: onRemove,
              customBorder: const CircleBorder(),
              child: const Padding(
                padding: EdgeInsets.all(4),
                child: Icon(
                  Icons.close_rounded,
                  size: 16,
                  color: AppColors.error,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _AddTile extends StatelessWidget {
  final VoidCallback onTap;

  const _AddTile({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width: 92,
        height: 92,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFE2E6F2), width: 1.5),
        ),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.add_photo_alternate_outlined,
              color: AppColors.lightPrimary,
            ),
            SizedBox(height: 4),
            Text(
              'Add',
              style: TextStyle(
                color: AppColors.lightPrimary,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
