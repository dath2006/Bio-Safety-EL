/** Shared food category definitions — labels shown in UI, slugs sent to API. */
export const FOOD_CATEGORIES = [
  { label: "Dairy Pasteurized",      slug: "dairy_pasteurized" },
  { label: "Ready-to-eat Meals",     slug: "rte"               },
  { label: "Catering & Food Service",slug: "catering"          },
  { label: "Meat & Poultry",         slug: "meat"              },
  { label: "Seafood & Fish",         slug: "seafood"           },
  { label: "Bakery & Confectionery", slug: "general"           },
  { label: "Beverages",              slug: "beverages"         },
  { label: "Spices & Condiments",    slug: "spices"            },
  { label: "Packaged Food",          slug: "packaged_food"     },
  { label: "Cold Chain / Frozen",    slug: "cold_chain"        },
  { label: "Street Food",            slug: "street_food"       },
] as const;

export type CategorySlug  = (typeof FOOD_CATEGORIES)[number]["slug"];
export type CategoryLabel = (typeof FOOD_CATEGORIES)[number]["label"];

/** Return slug for a given label (or the input as-is if already a slug). */
export function labelToSlug(labelOrSlug: string): string {
  const found = FOOD_CATEGORIES.find(
    (c) => c.label.toLowerCase() === labelOrSlug.toLowerCase()
  );
  return found ? found.slug : labelOrSlug.toLowerCase().replace(/\s+/g, "_");
}

/** Return display label for a slug. */
export function slugToLabel(slug: string): string {
  const found = FOOD_CATEGORIES.find((c) => c.slug === slug);
  return found ? found.label : slug;
}
