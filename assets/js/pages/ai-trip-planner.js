import {
  buildSuggestedItinerary,
} from "../app/ai/trip-planner-engine.js";

import {
  addTripItem,
  createTrip,
  listTripDestinationCatalogue,
} from "../app/api/trips-api.js";

import {
  bootstrap,
} from "../app/bootstrap.js";

import {
  createTripFromSuggestedItinerary,
} from "../app/ai/trip-planner-trip-creator.js";

import {
  enrichPlannerDestinationsWithAuthority,
  plannerRunPayload,
} from "../app/ai/planner-authority-adapter.js";

import {
  createPlannerRun,
  getDestinationPlannerProfile,
} from "../app/api/planner-api.js";

import {
  curatedDestinations,
} from "../data/curated-destinations.js";


function readCheckedValues(form, name) {
  return [...form.querySelectorAll(
    `input[name="${name}"]:checked`,
  )].map((input) => input.value);
}


function localizedDestinationName(destination, locale) {
  if (locale === "ar") {
    return (
      destination.name_ar ||
      destination.name_en ||
      destination.slug
    );
  }

  return (
    destination.name_en ||
    destination.name_ar ||
    destination.slug
  );
}


function localizedDestinationDescription(destination, locale) {
  if (locale === "ar") {
    return (
      destination.description_ar ||
      destination.description_en ||
      ""
    );
  }

  return (
    destination.description_en ||
    destination.description_ar ||
    ""
  );
}


function localizedCategory(destination, locale) {
  if (locale === "ar") {
    return (
      destination.category_ar ||
      destination.category_en ||
      ""
    );
  }

  return (
    destination.category_en ||
    destination.category_ar ||
    ""
  );
}


function localizedRegion(destination, locale) {
  if (locale === "ar") {
    return (
      destination.region_ar ||
      destination.region_en ||
      ""
    );
  }

  return (
    destination.region_en ||
    destination.region_ar ||
    ""
  );
}


function localizedDayLabel(dayNumber, locale) {
  return locale === "ar"
    ? `اليوم ${dayNumber}`
    : `Day ${dayNumber}`;
}


function localizedScoreLabel(locale) {
  return locale === "ar"
    ? "درجة التوافق"
    : "Match score";
}


function buildDestinationCard(destination, locale) {
  const article = document.createElement("article");
  article.className = "ai-planner-stop";

  const heading = document.createElement("h4");
  heading.textContent =
    localizedDestinationName(destination, locale);

  const meta = document.createElement("p");
  meta.className = "ai-planner-stop__meta";

  const category =
    localizedCategory(destination, locale);

  const region =
    localizedRegion(destination, locale);

  meta.textContent = [category, region]
    .filter(Boolean)
    .join(" · ");

  const description = document.createElement("p");
  description.textContent =
    localizedDestinationDescription(
      destination,
      locale,
    );

  const score = document.createElement("p");
  score.className = "ai-planner-stop__score";

  score.textContent =
    `${localizedScoreLabel(locale)}: ` +
    `${destination.planner_score?.total ?? 0}/90`;

  article.append(
    heading,
    meta,
    description,
    score,
  );

  return article;
}


function renderItinerary(root, itinerary, locale) {
  root.replaceChildren();

  const feasibility =
    renderTripFeasibility(
      itinerary,
      locale,
    );

  if (feasibility) {
    root.append(
      feasibility,
    );
  }

  const recommendations =
    renderTripRecommendations(
      itinerary,
      locale,
    );

  if (recommendations) {
    root.append(
      recommendations,
    );
  }

  const optimization =
    renderTripOptimization(
      itinerary,
      locale,
    );

  if (optimization) {
    root.append(
      optimization,
    );
  }

  const summary = document.createElement("div");
  summary.className = "ai-planner-result-summary";

  const title = document.createElement("h3");

  title.textContent = locale === "ar"
    ? "برنامج الرحلة المقترح"
    : "Suggested itinerary";

  const text = document.createElement("p");

  text.textContent = locale === "ar"
    ? `تم اختيار ${itinerary.selectedCount} وجهة موزعة على ${itinerary.requestedDays} يوم.`
    : `${itinerary.selectedCount} destinations selected across ${itinerary.requestedDays} days.`;

  const actions = document.createElement("div");
  actions.className = "ai-planner-result-actions";

  const createButton = document.createElement("button");
  createButton.type = "button";
  createButton.className = "primary-action";
  createButton.dataset.aiPlannerCreateTrip = "";

  createButton.textContent = locale === "ar"
    ? "إنشاء هذه الرحلة"
    : "Create this trip";

  const status = document.createElement("p");
  status.className = "ai-planner-create-status";
  status.dataset.aiPlannerCreateStatus = "";
  status.hidden = true;
  status.setAttribute("role", "status");

  actions.append(createButton, status);

  summary.append(title, text, actions);
  root.append(summary);

  createButton.addEventListener("click", async () => {
    if (createButton.disabled) {
      return;
    }

    createButton.disabled = true;

    status.hidden = false;
    status.textContent = locale === "ar"
      ? "جارٍ إنشاء الرحلة..."
      : "Creating your trip...";

    try {
      const context = await bootstrap();

      if (!context) {
        throw new Error("Application initialization failed");
      }

      const trip = await createTripFromSuggestedItinerary({
        itinerary,
        locale,
        apiEnabled: context.config.apiEnabled,
        authenticatedUser: context.session?.currentUser,
        listDestinationCatalogue:
          listTripDestinationCatalogue,
        createTrip,
        addTripItem,
      });

      const target =
        locale === "ar"
          ? `trip.html?id=${encodeURIComponent(trip.id)}`
          : `trip.html?id=${encodeURIComponent(trip.id)}`;

      globalThis.location.assign(target);
    } catch (error) {
      if (error?.code === "API_UNAVAILABLE") {
        status.textContent = locale === "ar"
          ? "إنشاء الرحلات غير متاح حاليًا في وضع العرض."
          : "Trip creation is currently unavailable in preview mode.";
      } else if (error?.code === "AUTH_REQUIRED") {
        status.textContent = locale === "ar"
          ? "يجب تسجيل الدخول أولًا لإنشاء الرحلة."
          : "Please sign in before creating this trip.";
      } else if (error?.code === "EMPTY_ITINERARY") {
        status.textContent = locale === "ar"
          ? "لا توجد وجهات كافية لإنشاء الرحلة."
          : "There are no destinations available to create this trip.";
      } else {
        console.error("AI Planner trip creation failed", error);

        status.textContent = locale === "ar"
          ? "تعذر إنشاء الرحلة. حاول مرة أخرى."
          : "The trip could not be created. Please try again.";
      }

      createButton.disabled = false;
    }
  });

  for (const day of itinerary.days) {
    const section = document.createElement("section");
    section.className = "ai-planner-day";

    const heading = document.createElement("h3");
    heading.textContent =
      localizedDayLabel(day.dayNumber, locale);

    section.append(heading);

    if (day.type === "travel") {
      const travelCard = document.createElement("div");
      travelCard.className = "ai-planner-travel-day";

      const travelTitle = document.createElement("h4");
      travelTitle.textContent = locale === "ar"
        ? "يوم انتقال"
        : "Travel day";

      const travelText = document.createElement("p");

      const fromRegion = String(
        day.fromRegion ?? "",
      );

      const toRegion = String(
        day.toRegion ?? "",
      );

      travelText.textContent = locale === "ar"
        ? `الانتقال من ${fromRegion} إلى ${toRegion}. تم تخصيص هذا اليوم للانتقال لتجنب برنامج سياحي مرهق أو غير واقعي.`
        : `Transfer from ${fromRegion} to ${toRegion}. This day is reserved for travel to avoid an unrealistic or exhausting itinerary.`;

      travelCard.append(
        travelTitle,
        travelText,
      );

      section.append(travelCard);
      root.append(section);
      continue;
    }

    if (day.type === "travel") {
      const travelCard = document.createElement("div");
      travelCard.className = "ai-planner-travel-day";

      const travelTitle = document.createElement("h4");
      travelTitle.textContent = locale === "ar"
        ? "يوم انتقال"
        : "Travel day";

      const travelText = document.createElement("p");

      const fromRegion = String(
        day.fromRegion ?? "",
      );

      const toRegion = String(
        day.toRegion ?? "",
      );

      travelText.textContent = locale === "ar"
        ? `الانتقال من ${fromRegion} إلى ${toRegion}. تم تخصيص هذا اليوم للانتقال لتجنب برنامج سياحي مرهق أو غير واقعي.`
        : `Transfer from ${fromRegion} to ${toRegion}. This day is reserved for travel to avoid an unrealistic or exhausting itinerary.`;

      travelCard.append(
        travelTitle,
        travelText,
      );

      section.append(travelCard);
      root.append(section);
      continue;
    }

    if (!day.destinations.length) {
      const empty = document.createElement("p");

      empty.textContent = locale === "ar"
        ? "لا توجد وجهات إضافية مقترحة لهذا اليوم."
        : "No additional destinations suggested for this day.";

      section.append(empty);
      root.append(section);
      continue;
    }

    const grid = document.createElement("div");
    grid.className = "ai-planner-stops";

    for (const destination of day.destinations) {
      grid.append(
        buildDestinationCard(
          destination,
          locale,
        ),
      );
    }

    section.append(grid);
    const summary =
      renderDaySummary(
        day,
        locale,
      );

    if (summary) {
      section.append(
        summary,
      );
    }

    const timeline =
      renderDayTimeline(
        day,
        locale,
      );

    if (timeline) {
      section.append(
        timeline,
      );
    }

    root.append(section);
  }
}


function initializePlanner() {
  const form = document.querySelector(
    "[data-ai-trip-planner-form]",
  );

  const resultRoot = document.querySelector(
    "[data-ai-trip-planner-result]",
  );

  if (!form || !resultRoot) {
    return;
  }

  const locale =
    document.documentElement.lang === "ar"
      ? "ar"
      : "en";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);

    const preferences = {
      days: Number(
        formData.get("days") || 3,
      ),

      startingPoint:
        formData.get("startingPoint") ||
        "tripoli",

      travelerType:
        formData.get("travelerType") ||
        "solo",

      pace:
        formData.get("pace") ||
        "balanced",

      interests:
        readCheckedValues(
          form,
          "interests",
        ),
    };

    let plannerDestinations =
      curatedDestinations;

    let plannerContext = null;

    try {
      const context = await bootstrap();
      plannerContext = context;

      if (context?.config?.apiEnabled) {
        plannerDestinations =
          await enrichPlannerDestinationsWithAuthority(
            curatedDestinations,
            {
              listDestinationCatalogue:
                listTripDestinationCatalogue,
              getDestinationPlannerProfile,
            },
          );
      }
    } catch (error) {
      console.warn(
        "AI Planner coordinate enrichment unavailable; using regional fallback.",
        error,
      );
    }

    const itinerary =
      buildSuggestedItinerary(
        plannerDestinations,
        preferences,
      );

    if (
      plannerContext?.config?.apiEnabled &&
      plannerContext?.session?.currentUser
    ) {
      createPlannerRun(plannerRunPayload(itinerary)).catch((error) => {
        if (plannerContext.config.debug) {
          console.warn("AI Planner run persistence unavailable; continuing locally.", error);
        }
      });
    }

    renderItinerary(
      resultRoot,
      itinerary,
      locale,
    );

    resultRoot.hidden = false;

    resultRoot.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });
}


document.addEventListener(
  "DOMContentLoaded",
  initializePlanner,
);
