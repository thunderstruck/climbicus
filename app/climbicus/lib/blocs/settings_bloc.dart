
import 'package:bloc/bloc.dart';
import 'package:climbicus/repositories/api_repository.dart';
import 'package:get_it/get_it.dart';
import 'package:package_info/package_info.dart';
import 'package:shared_preferences/shared_preferences.dart';


const DEFAULT_DISPLAY_PREDICTIONS_NUM = 3;
const PLACEHOLDER_GYM_ID = -1;
const DEFAULT_SEEN_CAMERA_HELP_OVERLAY = false;
const DEFAULT_SEEN_HOME_TUTORIAL = false;
const DEFAULT_SHOW_IMAGE_IDS = false;


class SettingsState {
  final int displayPredictionsNum;
  final int gymId;
  final PackageInfo? packageInfo;
  final bool seenCameraHelpOverlay;
  final bool seenHomeTutorial;
  final bool showImageIds;

  SettingsState({
    required this.displayPredictionsNum,
    required this.gymId,
    required this.packageInfo,
    required this.seenCameraHelpOverlay,
    required this.seenHomeTutorial,
    required this.showImageIds,
  });
}

class SettingsUninitialized extends SettingsState {
  SettingsUninitialized() : super(
    displayPredictionsNum: DEFAULT_DISPLAY_PREDICTIONS_NUM,
    gymId: PLACEHOLDER_GYM_ID,
    packageInfo: null,
    seenCameraHelpOverlay: DEFAULT_SEEN_CAMERA_HELP_OVERLAY,
    seenHomeTutorial: DEFAULT_SEEN_HOME_TUTORIAL,
    showImageIds: DEFAULT_SHOW_IMAGE_IDS,
  );
}

abstract class SettingsEvent {
  const SettingsEvent();
}

class InitializedSettings extends SettingsEvent {}

class GymChanged extends SettingsEvent {
  final int gymId;
  const GymChanged({required this.gymId});
}


class SettingsBloc extends Bloc<SettingsEvent, SettingsState> {
  final getIt = GetIt.instance;

  // Initialise settings with default values.
  String _imagePicker = "both";
  int _displayPredictionsNum = DEFAULT_DISPLAY_PREDICTIONS_NUM;
  int _gymId = PLACEHOLDER_GYM_ID;
  late PackageInfo _packageInfo;
  bool _seenCameraHelpOverlay = DEFAULT_SEEN_CAMERA_HELP_OVERLAY;
  bool _seenHomeTutorial = DEFAULT_SEEN_HOME_TUTORIAL;
  bool showImageIds = DEFAULT_SHOW_IMAGE_IDS;

  int get gymId => _gymId;

  int get displayPredictionsNum => _displayPredictionsNum;
  set displayPredictionsNum(int i) {
    _displayPredictionsNum = i;
    storeSetting("display_predictions_num", _displayPredictionsNum.toString());
  }

  bool get seenCameraHelpOverlay => _seenCameraHelpOverlay;
  set seenCameraHelpOverlay(bool v) {
    _seenCameraHelpOverlay = v;
    storeSetting("seen_camera_help_overlay", _seenCameraHelpOverlay.toString());
  }

  bool get seenHomeTutorial => _seenHomeTutorial;
  set seenHomeTutorial(bool v) {
    _seenHomeTutorial = v;
    storeSetting("seen_home_tutorial", _seenHomeTutorial.toString());
  }

  SettingsBloc() : super(SettingsUninitialized()) {
    retrieveSettings();
  }

  SettingsState createState() => SettingsState(
    displayPredictionsNum: _displayPredictionsNum,
    gymId: _gymId,
    packageInfo: _packageInfo,
    seenCameraHelpOverlay: _seenCameraHelpOverlay,
    seenHomeTutorial: _seenHomeTutorial,
    showImageIds: showImageIds,
  );

  Future<void> retrieveSettings() async {
    _imagePicker = await retrieveSetting("image_picker", _imagePicker);
    _displayPredictionsNum = int.parse(await retrieveSetting(
        "display_predictions_num", _displayPredictionsNum.toString()));
    _gymId = int.parse(await retrieveSetting("gym_id", _gymId.toString()));

    _packageInfo = await PackageInfo.fromPlatform();

    _seenCameraHelpOverlay = (await retrieveSetting("seen_camera_help_overlay",
      _seenCameraHelpOverlay.toString())) == "true";
    _seenHomeTutorial = (await retrieveSetting("seen_home_tutorial",
      _seenHomeTutorial.toString())) == "true";

    getIt<ApiRepository>().gymId = _gymId;

    add(InitializedSettings());
  }

  @override
  Stream<SettingsState> mapEventToState(SettingsEvent event) async* {
    if (event is InitializedSettings) {
      yield createState();
    } else if (event is GymChanged) {
      _gymId = event.gymId;
      getIt<ApiRepository>().gymId = _gymId;
      yield createState();
      storeSetting("gym_id", _gymId.toString());
    }
  }

  Future<void> storeSetting(String settingName, String val) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    prefs.setString(settingName, val);
  }

  Future<String> retrieveSetting(String settingName, String defaultVal) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    if (prefs.containsKey(settingName)) {
      return prefs.getString(settingName)!;
    }

    return defaultVal;
  }
}
