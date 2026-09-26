// Deterministic North Indian chart geometry and per-house planet slots.
//
// Every house has a verified list of slot centers. A planet label block
// (LABEL_BOX) placed at any slot is guaranteed to be:
//   - fully inside that house polygon (with a small margin),
//   - clear of the reserved rashi/sign-number box,
//   - clear of every other slot in the same house.
// The lists are ordered, so the first N slots are used for N planets and any
// prefix stays collision-free. House slots are shared with the geometry test
// in backend/tests so the renderer and the assertion cannot drift apart.
//
// This module contains presentation geometry only. It carries no astrology.

export type Point = [number, number];

export interface HouseGeometry {
  /** Polygon vertices in SVG coordinates (500x500 viewBox). */
  points: Point[];
  /** Reserved sign-number anchor. */
  rashi: Point;
  /** Ordered, collision-free planet slots. */
  slots: Point[];
}

/** Rendered planet label bounding box (planet abbreviation + degree + marker). */
export const LABEL_BOX = { width: 46, height: 16 };
/** Reserved box around the sign number that planet labels must not enter. */
export const RASHI_BOX = { width: 18, height: 18 };

export const HOUSE_GEOMETRY: Record<number, HouseGeometry> = {
  1: {
    points: [[250, 0], [125, 125], [250, 250], [375, 125]],
    rashi: [250, 62],
    slots: [[250, 140], [250, 124], [250, 156], [250, 108], [250, 172], [204, 140], [296, 140], [250, 92]],
  },
  2: {
    points: [[0, 0], [250, 0], [125, 125]],
    rashi: [135, 40],
    slots: [[105, 71], [103, 55], [121, 87], [103, 39], [151, 65], [105, 23], [167, 49], [59, 23]],
  },
  3: {
    points: [[0, 0], [125, 125], [0, 250]],
    rashi: [40, 135],
    slots: [[55, 105], [55, 89], [72, 121], [39, 73], [72, 137], [55, 153], [47, 169], [31, 185]],
  },
  4: {
    points: [[0, 250], [125, 125], [250, 250], [125, 375]],
    rashi: [62, 250],
    slots: [[140, 250], [140, 234], [140, 266], [140, 218], [140, 282], [94, 250], [186, 250], [140, 202]],
  },
  5: {
    points: [[0, 250], [125, 375], [0, 500]],
    rashi: [40, 365],
    slots: [[55, 395], [55, 411], [72, 379], [39, 427], [72, 363], [55, 347], [47, 331], [31, 315]],
  },
  6: {
    points: [[0, 500], [125, 375], [250, 500]],
    rashi: [135, 460],
    slots: [[105, 429], [103, 445], [121, 413], [103, 461], [151, 435], [105, 477], [167, 451], [59, 477]],
  },
  7: {
    points: [[250, 250], [125, 375], [250, 500], [375, 375]],
    rashi: [250, 438],
    slots: [[250, 360], [250, 344], [250, 376], [250, 328], [250, 392], [204, 360], [296, 360], [250, 312]],
  },
  8: {
    points: [[250, 500], [375, 375], [500, 500]],
    rashi: [365, 460],
    slots: [[394, 428], [397, 444], [378, 412], [397, 460], [348, 436], [397, 476], [351, 477], [333, 452]],
  },
  9: {
    points: [[375, 375], [500, 250], [500, 500]],
    rashi: [460, 365],
    slots: [[445, 395], [445, 411], [428, 379], [461, 427], [428, 363], [445, 347], [453, 331], [469, 315]],
  },
  10: {
    points: [[250, 250], [375, 125], [500, 250], [375, 375]],
    rashi: [438, 250],
    slots: [[360, 250], [360, 234], [360, 266], [360, 218], [360, 282], [314, 250], [406, 250], [360, 202]],
  },
  11: {
    points: [[375, 125], [500, 0], [500, 250]],
    rashi: [460, 135],
    slots: [[445, 105], [445, 89], [428, 121], [461, 73], [428, 137], [445, 153], [453, 169], [469, 185]],
  },
  12: {
    points: [[250, 0], [500, 0], [375, 125]],
    rashi: [365, 40],
    slots: [[394, 72], [397, 56], [378, 88], [397, 40], [348, 64], [397, 24], [351, 23], [333, 48]],
  },
};

export function polygonPoints(houseNumber: number): string {
  const geometry = HOUSE_GEOMETRY[houseNumber] ?? HOUSE_GEOMETRY[1];
  return geometry.points.map(([x, y]) => `${x},${y}`).join(' ');
}

/** Ordered slots for `count` planets, staying collision-free for every prefix. */
export function planetSlots(houseNumber: number, count: number): Point[] {
  const geometry = HOUSE_GEOMETRY[houseNumber] ?? HOUSE_GEOMETRY[1];
  if (count <= 0) return [];
  if (count <= geometry.slots.length) return geometry.slots.slice(0, count);
  // No house can hold more than 7 grahas (Rahu and Ketu are always opposite),
  // and every list holds at least 8, so overflow is unreachable in practice.
  return geometry.slots;
}
