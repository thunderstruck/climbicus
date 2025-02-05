import 'package:bloc/bloc.dart';
import 'package:climbicus/models/route_image.dart';
import 'package:climbicus/repositories/api_repository.dart';
import 'package:flutter/widgets.dart';
import 'package:get_it/get_it.dart';


class ImagesData {
  ImagesData(this.defaultRouteImageId, this.routeImages);

  int defaultRouteImageId;
  Map<int, RouteImage> routeImages;

  RouteImage? get defaultRouteImage => routeImages[defaultRouteImageId];
}

class Images {
  Map<int, ImagesData> _data = {};

  RouteImage? defaultImage(int routeId) {
    if (!_data.containsKey(routeId)) {
      return null;
    }

    return _data[routeId]!.defaultRouteImage;
  }

  Map<int, RouteImage>? allImages(int routeId) {
    if (!_data.containsKey(routeId)) {
      return null;
    }

    return _data[routeId]!.routeImages;
  }

  bool contains(int routeId) => _data.containsKey(routeId);

  void addRoutes(Map<int, RouteImage> routes) {
    _data.addAll(routes.map((routeId, routeImage) =>
        MapEntry(routeId, ImagesData(routeImage.id, {routeImage.id: routeImage})))
    );
  }

  void addRouteImages(int routeId, List<RouteImage> images) {
    if (!_data.containsKey(routeId)) {
      return;
    }

    _data[routeId]!.routeImages = Map.fromIterable(images,
      key: ((img) => img.id),
      value: ((img) => img),
    );
  }
}

abstract class RouteImagesEvent {
  const RouteImagesEvent();
}

class FetchRouteImages extends RouteImagesEvent {
  final List<int> routeIds;
  const FetchRouteImages({required this.routeIds});
}

class FetchRouteImagesAll extends RouteImagesEvent {
  final int routeId;
  const FetchRouteImagesAll({required this.routeId});
}

class AddNewRouteImage extends RouteImagesEvent {
  final int routeId;
  final RouteImage routeImage;
  const AddNewRouteImage({required this.routeId, required this.routeImage});
}

class UpdateRouteImage extends RouteImagesEvent {
  final int routeImageId;
  final int? routeId;
  const UpdateRouteImage({required this.routeImageId, this.routeId});
}

abstract class RouteImagesState {
  const RouteImagesState();
}

class RouteImagesUninitialized extends RouteImagesState {}

class RouteImagesLoading extends RouteImagesState {}

class RouteImagesLoaded extends RouteImagesState {
  final Images images;
  const RouteImagesLoaded({required this.images});
}

class RouteImagesError extends RouteImagesState {
  FlutterErrorDetails errorDetails;

  RouteImagesError({required Object exception, StackTrace? stackTrace}):
        errorDetails = FlutterErrorDetails(exception: exception, stack: stackTrace) {
    FlutterError.reportError(errorDetails);
  }
}

class RouteImagesBloc extends Bloc<RouteImagesEvent, RouteImagesState> {
  final getIt = GetIt.instance;

  final Images images = Images();

  RouteImagesBloc() : super(RouteImagesUninitialized());

  @override
  Stream<RouteImagesState> mapEventToState(RouteImagesEvent event) async* {
    if (event is FetchRouteImages) {
      yield RouteImagesLoading();

      var routeIds = event.routeIds;

      // Do not fetch already present route images.
      routeIds.removeWhere((id) => images.contains(id));
      if (routeIds.isEmpty) {
        yield RouteImagesLoaded(images: images);
        return;
      }

      try {
        Map<String, dynamic> routeImages =
            (await getIt<ApiRepository>().fetchRouteImages(routeIds))["route_images"];
        var fetchedImages = routeImages.map((routeId, model) =>
            MapEntry(int.parse(routeId), RouteImage.fromJson(model)));
        images.addRoutes(fetchedImages);

        yield RouteImagesLoaded(images: images);
        return;
      } catch (e, st) {
        yield RouteImagesError(exception: e, stackTrace: st);
      }
    } else if (event is FetchRouteImagesAll) {
      yield RouteImagesLoading();

      try {
        List<dynamic> routeImages =
            (await getIt<ApiRepository>().fetchRouteImagesAllRoute(event.routeId))["route_images"];
        var fetchedImages = routeImages.map((model) => RouteImage.fromJson(model)).toList();
        images.addRouteImages(event.routeId, fetchedImages);

        yield RouteImagesLoaded(images: images);
      } catch (e, st) {
        yield RouteImagesError(exception: e, stackTrace: st);
      }
    } else if (event is AddNewRouteImage) {
      // Not uploading image to the database via API because all images are
      // uploaded as part of predictions at the moment.
      getIt<ApiRepository>().routeMatch(event.routeImage.id, event.routeId);

      images.addRoutes({event.routeId: event.routeImage});

      yield RouteImagesLoaded(images: images);
    } else if (event is UpdateRouteImage) {
      getIt<ApiRepository>().routeMatch(event.routeImageId, event.routeId);
      // TODO: update 'images' in case of no routeId

      yield RouteImagesLoaded(images: images);
    }

    return;
  }
}
