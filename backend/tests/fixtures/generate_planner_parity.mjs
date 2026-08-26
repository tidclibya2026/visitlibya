import fs from "node:fs";
import {
  scheduleDestinationSequence,
} from "../../../assets/js/app/ai/opening-hours-intelligence.js";
import { insertMealAndRestStops } from "../../../assets/js/app/ai/meal-rest-intelligence.js";
import { visitDurationMinutes } from "../../../assets/js/app/ai/visit-duration-intelligence.js";
import { estimatedTravelMinutes } from "../../../assets/js/app/ai/travel-time-intelligence.js";
import { roadFeasibilityEvidence } from "../../../assets/js/app/ai/road-feasibility.js";
import { optimizeItineraryStructure, optimizationSummary } from "../../../assets/js/app/ai/trip-auto-optimization.js";
import { applyPlannerProfile } from "../../../assets/js/app/ai/planner-authority-adapter.js";

const inputPath = new URL("./planner_parity_inputs.json", import.meta.url);
const cases = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const output = {};
for (const item of cases) {
  if (item.authority) {
    const authority = item.authority;
    const translation = authority.translations.find(({ language_code }) => language_code === "en") ?? {};
    const destination = { destination_id: authority.destination_id, slug: authority.slug, category_key: authority.category_code, latitude: authority.latitude, longitude: authority.longitude, name_en: translation.name, description_en: translation.short_description, region_en: authority.region };
    const op = authority.operational_data;
    const profile = { destination_id: authority.destination_id, opening_hours: op.opening_hours, recommended_visit_minutes: op.recommended_visit_minutes, planner_priority: op.planner_priority, access_status: op.access_status, road_access: op.road_access, road_surface: op.road_surface, road_condition: op.road_condition, meal_suitability: op.meal_suitability, rest_suitability: op.rest_suitability, verification_status: authority.profile_verification_status, verified_at: authority.profile_verified_at };
    const normalized = applyPlannerProfile(destination, profile);
    normalized.planner_authority.profileState = authority.profile_state;
    output[item.id] = { slug: normalized.slug, visitMinutes: visitDurationMinutes(normalized, item.pace), opening: [normalized.opening_time, normalized.closing_time], authority: normalized.planner_authority };
    continue;
  }
  if (item.optimization) {
    const result = optimizeItineraryStructure(item.optimization);
    output[item.id] = { actions: result.actions, summary: optimizationSummary(result), optimizedSlugs: result.optimizedDays[0].destinations.map(({ slug }) => slug) };
    continue;
  }
  const scheduled = scheduleDestinationSequence({ destinations: item.destinations, pace: item.pace, visitDurationResolver: visitDurationMinutes });
  const breaks = insertMealAndRestStops({ scheduledItems: scheduled, pace: item.pace }).filter(({ type }) => type === "meal" || type === "rest").map(({ type }) => type);
  output[item.id] = {
    visits: scheduled.map(({ destination, scheduled, reason, startsAt, endsAt, visitMinutes }) => ({ slug: destination.slug, scheduled, reason, startsAt, endsAt, visitMinutes })),
    breaks,
    travelMinutes: item.destinations.length > 1 ? estimatedTravelMinutes(item.destinations[0], item.destinations[1]) : null,
    road: item.destinations.map((destination) => roadFeasibilityEvidence(destination)),
  };
}
process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
