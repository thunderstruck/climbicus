import 'package:climbicus/blocs/gym_areas_bloc.dart';
import 'package:climbicus/blocs/gym_routes_bloc.dart';
import 'package:climbicus/blocs/route_images_bloc.dart';
import 'package:climbicus/blocs/user_route_log_bloc.dart';
import 'package:climbicus/blocs/users_bloc.dart';
import 'package:climbicus/models/app/route_user_meta.dart';
import 'package:climbicus/models/user.dart';
import 'package:climbicus/models/user_route_log.dart';
import 'package:climbicus/repositories/user_repository.dart';
import 'package:climbicus/utils/time.dart';
import 'package:climbicus/widgets/rating_star.dart';
import 'package:climbicus/widgets/route_image_carousel.dart';
import 'package:climbicus/widgets/route_log.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import '../style.dart';

class RouteDetailedArgs {
  final RouteWithUserMeta routeWithUserMeta;

  RouteDetailedArgs(this.routeWithUserMeta);
}

class RouteDetailedPage extends StatefulWidget {
  static const routeName = '/route_detailed';
  
  final getIt = GetIt.instance;

  final RouteDetailedArgs args;

  RouteDetailedPage(this.args);

  @override
  State<StatefulWidget> createState() => _RouteDetailedPage();
}

class _RouteDetailedPage extends State<RouteDetailedPage> {
  late RouteImagesBloc _routeImagesBloc;
  late UserRouteLogBloc _userRouteLogBloc;
  late GymRoutesBloc _gymRoutesBloc;

  @override
  void initState() {
    super.initState();

    _routeImagesBloc = BlocProvider.of<RouteImagesBloc>(context);
    _routeImagesBloc.add(FetchRouteImagesAll(routeId: widget.args.routeWithUserMeta.route.id));

    _userRouteLogBloc = BlocProvider.of<UserRouteLogBloc>(context);
    _userRouteLogBloc.add(FetchUserRouteLog(routeId: widget.args.routeWithUserMeta.route.id));

    _gymRoutesBloc = BlocProvider.of<GymRoutesBloc>(context);
  }

  @override
  Widget build(BuildContext context) {
    var routeTitleName = widget.args.routeWithUserMeta.route.name ??
        '${widget.args.routeWithUserMeta.route.grade} route';
    var userId = widget.args.routeWithUserMeta.route.userId;

    return Scaffold(
      appBar: AppBar(
        title: Text(routeTitleName),
      ),
      body: Column(
        children: <Widget>[
          Container(
            height: 200.0,
            child: BlocBuilder<RouteImagesBloc, RouteImagesState>(
              builder: (context, state) {
                if (state is RouteImagesLoaded) {
                  return RouteImageCarousel(
                    images: state.images.allImages(widget.args.routeWithUserMeta.route.id),
                  );
                } else if (state is RouteImagesError) {
                  return ErrorWidget.builder(state.errorDetails);
                }

                return Center(child: CircularProgressIndicator());
              },
            ),
          ),
          decorateLogWidget(context, _buildRouteVotes()),
          decorateLogWidget(context, _buildRouteDetails(userId), height: null, padding: 10),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    "Activity:",
                    style: TextStyle(fontSize: HEADING_SIZE_3),
                  ),
                  Expanded(
                    child: _buildRouteAscents(),
                  ),
                ],
              ),
            ),
          ),
        ],
      )
    );
  }

  Widget _buildRouteVotes() {
    return BlocBuilder<GymRoutesBloc, GymRoutesState>(
      builder: (context, state) {
        if (state is GymRoutesLoaded) {
          return Row(
            children: [
              Expanded(
                  child: gradeAndDifficulty(widget.args.routeWithUserMeta, 80.0)
              ),
              Expanded(
                  child: qualityAndAscents(context, widget.args.routeWithUserMeta, 80.0)
              ),
            ],
          );
        } else if (state is GymRoutesError) {
          return ErrorWidget.builder(state.errorDetails);
        }

        return Center(child: CircularProgressIndicator());
      },
    );
  }

  Widget _buildRouteDetails(int userId) {
    return BlocBuilder<UsersBloc, UsersState>(
      builder: (context, state) {
        if (state is UsersLoaded && state.users.loadResources({userId})) {
          var userName = state.users.getResource(userId)!.name;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                "Added by: $userName",
                style: TextStyle(fontSize: HEADING_SIZE_3),
              ),
              Text(
                "Added on: ${dateToString(widget.args.routeWithUserMeta.route.createdAt)}",
                style: TextStyle(fontSize: HEADING_SIZE_3),
              ),
              Text(
                "Category: ${widget.args.routeWithUserMeta.route.category}",
                style: TextStyle(fontSize: HEADING_SIZE_3),
              ),
              BlocBuilder<GymAreasBloc, GymAreasState>(
                builder: (context, state) {
                  if (state is GymAreasLoaded) {
                    return Text(
                      "Area: ${state.areas[widget.args.routeWithUserMeta.route.areaId]!.name}",
                      style: TextStyle(fontSize: HEADING_SIZE_3),
                    );
                  } else if (state is GymAreasError) {
                    return ErrorWidget.builder(state.errorDetails);
                  }

                  return Center(child: CircularProgressIndicator());
                },
              ),
            ],
          );
        } else if (state is UsersError) {
          return ErrorWidget.builder(state.errorDetails);
        }

        return Center(child: CircularProgressIndicator());
      },
    );
  }

  Widget _buildRouteAscents() {
    return BlocBuilder<UserRouteLogBloc, UserRouteLogState>(
      builder: (context, userRouteLogState) {
        if (userRouteLogState is UserRouteLogLoaded) {
          // Keep waiting if this route's logs haven't been fetched yet.
          var userRouteLogs = userRouteLogState.userRouteLogs[widget.args.routeWithUserMeta.route.id];
          if (userRouteLogs != null) {
            var userIds = userRouteLogs.values.map((e) => e.userId).toSet();

            return BlocBuilder<UsersBloc, UsersState>(
              builder: (context, usersState) {
                if (usersState is UsersLoaded && usersState.users.loadResources(userIds)) {
                  return _buildRouteAscentsWithUsers(
                    usersState.users,
                    userRouteLogs,
                  );
                } else if (usersState is UsersError) {
                  return ErrorWidget.builder(usersState.errorDetails);
                }

                return Center(child: CircularProgressIndicator());
              },
            );
          }
        } else if (userRouteLogState is UserRouteLogError) {
          return ErrorWidget.builder(userRouteLogState.errorDetails);
        }

        return Center(child: CircularProgressIndicator());
      },
    );
  }

  Widget? _buildDeleteButton(UserRouteLog userRouteLog) {
    if (widget.getIt<UserRepository>().userId != userRouteLog.userId) {
      return null;
    }

    return IconButton(
      icon: const Icon(Icons.delete_outline),
      onPressed: () async {
        _userRouteLogBloc.add(DeleteUserRouteLog(userRouteLog: userRouteLog));
        _gymRoutesBloc.add(DeleteUserLog(userRouteLog: userRouteLog));
      },
    );
  }

  Widget _buildRouteAscentsWithUsers(Users users,
      Map<int, UserRouteLog> userRouteLogs) {
    List<Widget> ascents = [];
    for (var userRouteLog in userRouteLogs.values) {
      var user = users.getResource(userRouteLog.userId)!.name;
      ascents.add(
        ListTile(
          leading: AscentWidget(userRouteLog),
          title: Text(user),
          subtitle: Text(dateToString(userRouteLog.createdAt)),
          trailing: _buildDeleteButton(userRouteLog),
        )
      );
    }

    if (ascents.isEmpty) {
      ascents.add(
          ListTile(title: Text(
            "No ascents yet..",
            style: TextStyle(fontSize: HEADING_SIZE_3),
          ))
      );
    }

    var scrollController = ScrollController();
    return Scrollbar(
      isAlwaysShown: true,
      controller: scrollController,
      child: ListView.separated(
        controller: scrollController,
        padding: const EdgeInsets.all(8),
        itemCount: ascents.length,
        itemBuilder: (context, index) => ascents[index],
        separatorBuilder: (context, index) => Divider(),
      ),
    );
  }
}
