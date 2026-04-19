export const nodeTypes = [
  { type: "character",    label: "Character",    pluralLabel: "Characters"    },
  { type: "race",         label: "Race",         pluralLabel: "Races"         },
  { type: "location",     label: "Location",     pluralLabel: "Locations"     },
  { type: "event",        label: "Event",        pluralLabel: "Events"        },
  { type: "organization", label: "Organization", pluralLabel: "Organizations" },
  { type: "timeline",     label: "Timeline",     pluralLabel: "Timelines"     },
  { type: "item",         label: "Item",         pluralLabel: "Items"         },
  { type: "language",     label: "Language",     pluralLabel: "Languages"     },
  { type: "script",       label: "Script",       pluralLabel: "Scripts"       }
];

export const relationTypes = [
  { type: "BELONGS_TO_RACE", label: "Belongs to race",   from: ["character"], to: ["race"] },
  { type: "MEMBER_OF",       label: "Member of",         from: ["character"], to: ["organization"] },
  { type: "PARTICIPATED_IN", label: "Participated in",   from: ["character"], to: ["event"] },
  { type: "BORN_IN",         label: "Born in",           from: ["character"], to: ["location"] },
  { type: "LIVED_IN",        label: "Lived in",          from: ["character"], to: ["location"] },
  { type: "KNOWS",           label: "Knows",             from: ["character"], to: ["character"] },
  { type: "PARENT_OF",       label: "Parent of",         from: ["character"], to: ["character"] },
  { type: "CHILD_OF",        label: "Child of",          from: ["character"], to: ["character"] },
  { type: "OWNS",            label: "Owns",              from: ["character"], to: ["item"] },
  { type: "RULED_BY",        label: "Ruled by",          from: ["location"],  to: ["character"] },
  { type: "LOCATED_IN",      label: "Located in",        from: ["location"],  to: ["location"] },
  { type: "HAPPENED_IN",     label: "Happened in",       from: ["event"],     to: ["location"] },
  { type: "SPEAKS",          label: "Speaks",            from: ["character", "race"], to: ["language"] },
  { type: "DURING",          label: "During",            from: ["event"],     to: ["timeline"] },
  { type: "PART_OF",         label: "Part of",           from: ["event"],     to: ["event"] },
  { type: "IN_CATEGORY",     label: "In category",       from: ["character", "location", "event", "organization", "item", "race", "timeline", "language", "script"], to: ["category"] }
];