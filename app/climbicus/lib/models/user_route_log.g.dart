// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_route_log.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserRouteLog _$UserRouteLogFromJson(Map<String, dynamic> json) {
  return UserRouteLog(
    json['id'] as int,
    json['route_id'] as int,
    json['user_id'] as int,
    json['gym_id'] as int,
    json['completed'] as bool,
    json['num_attempts'] as int?,
    DateTime.parse(json['created_at'] as String),
  );
}

Map<String, dynamic> _$UserRouteLogToJson(UserRouteLog instance) =>
    <String, dynamic>{
      'id': instance.id,
      'route_id': instance.routeId,
      'user_id': instance.userId,
      'gym_id': instance.gymId,
      'completed': instance.completed,
      'num_attempts': instance.numAttempts,
      'created_at': instance.createdAt.toIso8601String(),
    };
