import fs from "node:fs";
import { applyPlannerProfile } from "../../../assets/js/app/ai/planner-authority-adapter.js";
import { buildSuggestedItinerary } from "../../../assets/js/app/ai/trip-planner-engine.js";

const cases = JSON.parse(fs.readFileSync(new URL("./planner_full_parity_inputs.json", import.meta.url), "utf8"));
const normalize = (authority) => {
  const translation = authority.translations.find(({ language_code }) => language_code === "en") ?? {};
  const base = { destination_id: authority.destination_id, slug: authority.slug, category_key: authority.category_code, name_en: translation.name, description_en: translation.short_description, region_en: authority.region };
  if (authority.latitude !== null && authority.longitude !== null) {
    base.latitude = authority.latitude; base.longitude = authority.longitude;
  }
  const op = authority.operational_data ?? {};
  const profile = { destination_id: authority.destination_id, opening_hours: op.opening_hours, recommended_visit_minutes: op.recommended_visit_minutes, planner_priority: op.planner_priority, access_status: op.access_status, road_access: op.road_access, road_surface: op.road_surface, road_condition: op.road_condition, meal_suitability: op.meal_suitability, rest_suitability: op.rest_suitability, verification_status: authority.profile_verification_status, verified_at: authority.profile_verified_at };
  const result = applyPlannerProfile(base, profile); result.planner_authority.profileState = authority.profile_state; return result;
};
const project = (result) => ({
  days: result.days.map((day) => ({ dayNumber: day.dayNumber, type: day.type, slugs: day.destinations.map(({ slug }) => slug), timeline: (day.timeline ?? []).map((item) => ({ type: item.type, slug: item.destination?.slug ?? null, scheduled: item.scheduled ?? null, conflictAdjusted: item.conflictAdjusted ?? null })), summary: day.summary ?? null })),
  scores: result.days.flatMap((day) => day.destinations.map(({ slug, planner_score }) => ({ slug, total: planner_score.total, interestScore: planner_score.interestScore, geographicPenalty: planner_score.geographicPenalty, routingMode: planner_score.routingMode, authority: planner_score ? day.destinations.find((item) => item.slug === slug)?.planner_authority : null }))),
  feasibility: result.feasibility,
  recommendationCodes: result.recommendations.recommendations.map(({ code }) => code),
  optimization: { actions: result.optimization.actions, summary: result.optimization.summary, improvement: result.optimization.improvement, beforeScore: result.optimization.before.feasibility.score, afterScore: result.optimization.after.feasibility.score },
  selectedCount: result.selectedCount,
});
const output = Object.fromEntries(cases.map((item) => [item.id, project(buildSuggestedItinerary(item.destinations.map(normalize), item.preferences))]));
process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
