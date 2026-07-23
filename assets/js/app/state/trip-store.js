const DEFAULT_STATE = Object.freeze({
  trips: Object.freeze([]),
  selectedTrip: null,
  loading: false,
  saving: false,
  error: null,
  pagination: Object.freeze({ skip: 0, limit: 20, total: 0 }),
  filters: Object.freeze({}),
  locale: "en",
  authenticatedUser: null,
});

function freezeState(state) {
  return Object.freeze({
    ...state,
    trips: Object.freeze([...(state.trips ?? [])]),
    pagination: Object.freeze({ ...(state.pagination ?? {}) }),
    filters: Object.freeze({ ...(state.filters ?? {}) }),
  });
}

export function createTripStore(initialState = {}) {
  let state = freezeState({ ...DEFAULT_STATE, ...initialState });
  const subscribers = new Set();
  let destroyed = false;

  const publish = () => {
    subscribers.forEach((subscriber) => subscriber(state));
  };

  return Object.freeze({
    getState() {
      return state;
    },
    setState(nextState) {
      if (destroyed) return state;
      state = freezeState({ ...DEFAULT_STATE, ...nextState });
      publish();
      return state;
    },
    updateState(patch) {
      if (destroyed) return state;
      const update = typeof patch === "function" ? patch(state) : patch;
      state = freezeState({ ...state, ...update });
      publish();
      return state;
    },
    subscribe(subscriber) {
      if (destroyed || typeof subscriber !== "function") {
        throw new TypeError("Store subscriber must be a function");
      }
      subscribers.add(subscriber);
      return () => subscribers.delete(subscriber);
    },
    destroy() {
      subscribers.clear();
      destroyed = true;
    },
  });
}
