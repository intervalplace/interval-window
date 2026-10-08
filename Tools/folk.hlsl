// THE MASTER MATERIAL FOR IMPORTED ART.
//
// The glTF importer parents everything it brings in to Unreal's Substrate
// master material, and Substrate is not enabled in this project -- so every
// figure came in with its textures correctly assigned and rendered flat grey.
// It looks exactly like a missing texture and is nothing of the sort.
//
// Re-parenting to this costs one material and buys something back: `Tint`.
// The art gives one villager; the world gives thousands of citizens, each with
// a key of their own, and the key can colour the cloth without touching the
// art. The browser window derives a hue the same way from the same digits, so
// a person is recognisably themselves in either window.

float3 C = Base;

// Tint only what is CLOTH. Skin, leather and metal want to stay the colour
// the artist painted them, or everyone in a blue tunic also has blue hands.
// Cloth on this atlas is the mid-saturation, mid-value range; skin is pale and
// warm, leather and iron are dark and nearly grey.
float Mx = max(C.r, max(C.g, C.b));
float Mn = min(C.r, min(C.g, C.b));
float Sat = (Mx > 0.001) ? (Mx - Mn) / Mx : 0.0;

float IsCloth = smoothstep(0.10, 0.26, Sat) * smoothstep(0.02, 0.09, Mx)
              * (1.0 - smoothstep(0.34, 0.62, Mx));

// The tunic takes the citizen's hue at the brightness the artist chose, so a
// dyed garment still reads as the same garment in the same light.
float3 Dyed = Tint * (Mx / max(0.001, max(Tint.r, max(Tint.g, Tint.b))));
C = lerp(C, Dyed, IsCloth * Strength);

Rough = 0.86;
return C;
