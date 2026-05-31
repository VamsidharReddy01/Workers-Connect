class WorkerWorkImageModel {
  final int id;
  final String imageUrl;
  final String? caption;
  final int sortOrder;

  WorkerWorkImageModel({
    required this.id,
    required this.imageUrl,
    this.caption,
    required this.sortOrder,
  });

  factory WorkerWorkImageModel.fromJson(Map<String, dynamic> json) {
    return WorkerWorkImageModel(
      id: json['id'] as int,
      imageUrl: json['image_url'] as String,
      caption: json['caption'] as String?,
      sortOrder: json['sort_order'] as int? ?? 0,
    );
  }
}
