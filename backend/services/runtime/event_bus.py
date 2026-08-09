from blinker import Namespace

# Runtime Events Namespace
runtime_signals = Namespace()

activity_created = runtime_signals.signal('activity-created')
activity_scheduled = runtime_signals.signal('activity-scheduled')
activity_started = runtime_signals.signal('activity-started')
activity_paused = runtime_signals.signal('activity-paused')
activity_resumed = runtime_signals.signal('activity-resumed')
activity_extended = runtime_signals.signal('activity-extended')
activity_completed = runtime_signals.signal('activity-completed')
activity_skipped = runtime_signals.signal('activity-skipped')
activity_missed = runtime_signals.signal('activity-missed')
activity_interrupted = runtime_signals.signal('activity-interrupted')
activity_recovered = runtime_signals.signal('activity-recovered')

def get_signal_by_name(name: str):
    mapping = {
        'ActivityCreated': activity_created,
        'ActivityScheduled': activity_scheduled,
        'ActivityStarted': activity_started,
        'ActivityPaused': activity_paused,
        'ActivityResumed': activity_resumed,
        'ActivityExtended': activity_extended,
        'ActivityCompleted': activity_completed,
        'ActivitySkipped': activity_skipped,
        'ActivityMissed': activity_missed,
        'ActivityInterrupted': activity_interrupted,
        'ActivityRecovered': activity_recovered,
        'TransitionedToRUNNING': activity_started,
        'TransitionedToPAUSED': activity_paused,
        'TransitionedToCOMPLETED_MANUAL': activity_completed,
        'TransitionedToCOMPLETED_AUTO': activity_completed,
        'TransitionedToSKIPPED': activity_skipped,
        'TransitionedToMISSED': activity_missed,
        'TransitionedToINTERRUPTED': activity_interrupted,
        'TransitionedToSCHEDULED': activity_scheduled
    }
    return mapping.get(name)
