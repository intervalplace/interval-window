// A WING BEAT, AS A VERTEX OFFSET.
//
// The same idea as `wind.hlsl` and for the same reason: the bird is a static
// mesh, there are two dozen of them in the air at once, and a rig with a
// skeleton and an animation for each would be three orders of magnitude more
// machinery than a sine wave. What makes a bird read as a bird at this
// distance is not anatomy, it is that the wings MOVE -- the same lesson the
// hanging chain taught, written down in the note over `hang.hlsl`.
//
// THE OFFSET IS BUILT FROM THE OBJECT'S OWN AXES, not from world ones. A bird
// heads wherever it is going and the flap is up and down RELATIVE TO THE BIRD;
// offsetting along world Z would be right only for a bird flying level and
// would shear the wings off one banking. `Up`, `Side` and `Fore` are the
// instance's local axes carried into world space by the material, exactly as
// the chain's swing plane is.

// HOW FAR OUT THE WING THIS VERTEX IS. Nought at the breastbone, one at the
// tip. Raised to a power so the wing bends in a curve rather than pivoting
// like a plank: the outer third of a wing does nearly all the travelling.
float Out  = saturate(abs(Local.y) / max(Span, 1.0));
float Wing = pow(Out, 1.5);

// ---- THE BEAT ----
//
// Each bird has its own phase, off `PerInstanceRandom`, or a flock beats as
// one animal and reads as a decal.
float T = Time * max(Rate, 0.01) + Phase * 7.0;
float Beat = sin(T * 6.28318);

// A WING SNAPS DOWN AND RECOVERS. A pure sine is symmetrical and a bird is
// not: the downstroke is the one that does the work and it is quicker. The
// odd power sharpens both halves without changing the sign, and the small
// asymmetry below makes the down half the faster one.
Beat = sign(Beat) * pow(abs(Beat), 0.72);
Beat = Beat * (Beat < 0.0 ? 1.15 : 0.85);

// ---- AND THEY DO NOT FLAP ALL THE TIME ----
//
// A bird that beats steadily for ever is a wind-up toy. Real ones flap, then
// set their wings and glide, then flap again -- and the glide is most of what
// says "bird" from a long way off, because it is the only moment the
// silhouette holds still long enough to be read.
float Glide = 0.28 + 0.72 * saturate(sin(T * 0.11 + Phase * 23.0) * 1.7 + 0.35);
float Swing = Beat * Amp * Glide;

// The tip travels furthest; the body rides the other way a little, which is
// what makes the whole animal look like it is being held up by the wings
// rather than the wings being waved at the side of it.
float Lift = Wing * Swing;
float Bob  = (1.0 - Wing) * Swing * -0.16;

// AND THE WING DRAWS IN AS IT RISES. A wing that only goes up and down is a
// paper aeroplane being waggled; a real one folds a little at the top of the
// stroke, and in silhouette that shortening is half of what the eye reads.
float Fold = -sign(Local.y) * Wing * abs(Beat) * Amp * 0.13 * Glide;

return Up * (Lift + Bob) + Side * Fold;
