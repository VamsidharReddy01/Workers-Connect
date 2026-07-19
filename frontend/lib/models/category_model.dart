class CategoryModel {
  final String name;
  final int workerCount;

  CategoryModel({required this.name, required this.workerCount});

  factory CategoryModel.fromJson(Map<String, dynamic> json) {
    return CategoryModel(
      name: json['category'] as String,
      workerCount: json['worker_count'] as int,
    );
  }
}
