export type Property = {
  property_id: string;
  postcode: string;
  city: string;
  area: string;
  property_type: string;
  bedrooms: number;
  bathrooms: number;
  rent_pcm: number;
  size_sqft: number;
  furnished: boolean;
  parking: boolean;
  garden: boolean;
  balcony: boolean;
  pets_allowed: boolean;
  available_date: string;
  amenities: string;
  description: string;
  latitude: number;
  longitude: number;
};

export type Applicant = {
  applicant_id: string;
  name: string;
  age_band: string;
  budget_min: number;
  budget_max: number;
  preferred_areas: string;
  bedrooms_required: number;
  property_types: string;
  move_in_date: string;
  employment_type: string;
  pets: boolean;
  children: boolean;
  furnished_preference: string;
  parking_required: boolean;
  amenities_preferences: string;
};

export type Citation = {
  source: string;
  document_type: string;
  applicant_id?: string;
  property_id?: string;
  timestamp?: string;
  excerpt: string;
  score: number;
};

export type PropertyMatch = {
  property: Property;
  match_score: number;
  explanation: {
    positives: string[];
    negatives: string[];
    budget_match: number;
    bedroom_match: number;
    location_match: number;
    amenity_match: number;
  };
};

export type ApplicantIntelligence = {
  applicant: Applicant;
  top_matches: PropertyMatch[];
  intent: { intent: string; confidence: number; key_signals: string[]; features: Record<string, number> };
  conversion: { conversion_probability: number; top_positive_factors: string[]; top_negative_factors: string[] };
  key_signals: string[];
  recommended_action: {
    action: string;
    priority: string;
    confidence: number;
    reason: string;
    recommended_properties: PropertyMatch[];
  };
  explanation: string;
  sources: Citation[];
};

export type PropertyIntelligence = {
  property: Property;
  demand: string;
  qualified_applicants: number;
  strong_matches: number;
  average_match_score: number;
  viewing_conversion: number;
  application_conversion: number;
  top_applicant_concern: string;
  top_applicant_preference: string;
  popular_amenities: string[];
  applicant_segments: Record<string, number>;
  recommended_action: string;
  top_matching_applicants: Array<{ applicant_id: string; name: string; match_score: number }>;
  sources: Citation[];
};
