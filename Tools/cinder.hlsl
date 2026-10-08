// EMBERS IN THE CRACKS OF A BURNT CROWN.
//
// The cinder-crown falls from the dragon, one in two thousand and forty-eight,
// and `engine.js` §6da is blunt about what it does: "worn on the head, defends
// nothing -- pure cosmetic". A cosmetic whose entire purpose is to be seen has
// one job, and it should do it after dark as well as before.
//
// SO THE SPLITS BETWEEN THE LUMPS ARE STILL ALIGHT. Not the whole crown, which
// would be a lamp on somebody's head: eighteen faces of four hundred, deep in
// the fissures, which is where a draught would still be reaching a day after
// the fire went out.
//
// ADDITIVE AND UNLIT, so what this returns is what lands on the frame, over
// whatever the burnt stone beside it is doing. The same relation the stars
// have to the sky.

// ---- THE BREATH ----
//
// A coal does not flicker like a flame; it swells and fades. Two sines whose
// periods do not divide into one another, so the pattern never repeats
// anywhere a person would notice, and neither of them is fast enough to read
// as a strobe.
float Slow = 0.5 + 0.5 * sin(Time * 0.71);
float Under = 0.5 + 0.5 * sin(Time * 1.13 + 2.1);
float Breath = 0.62 + 0.38 * (Slow * 0.68 + Under * 0.32);

// AND BRIGHTER IN THE DARK, which is not a trick: an ember is the same
// brightness at noon and midnight and only one of those has anything to
// compete with. At full day it is a warm line in a crack; at night it is the
// thing that picks a citizen out of a market square, which is the whole point
// of owning one.
float Dark = saturate(Night);
float Lift = lerp(0.30, 1.0, Dark);

// The colour runs from the deep red of stone that is barely holding heat to
// the orange of a coal that has just been breathed on, so the crown shifts
// hue as it swells rather than just getting brighter. A light that only
// changes in brightness reads as an opacity being animated, which is what it
// would in fact be.
float3 Cool = float3(0.42, 0.06, 0.01);
float3 Hot  = float3(1.00, 0.44, 0.10);
float3 Coal = lerp(Cool, Hot, Breath * Breath);

return Coal * Breath * Lift * max(Bright, 0.0);
