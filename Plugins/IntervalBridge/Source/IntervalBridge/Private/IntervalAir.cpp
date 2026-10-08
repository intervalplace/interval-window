// Copyright interval.

#include "IntervalAir.h"

#include "Components/PostProcessComponent.h"
#include "IntervalLook.h"

AIntervalAir::AIntervalAir()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Air = CreateDefaultSubobject<UPostProcessComponent>(TEXT("Air"));
	Air->SetupAttachment(RootComponent);
	Air->bUnbound = true;          // the whole world, not a box in it
	Air->Priority = 10.f;          // over anything the level already carries
}

void AIntervalAir::BeginPlay()
{
	Super::BeginPlay();
	Compose();
}

void AIntervalAir::Compose()
{
	if (!Air)
	{
		return;
	}
	FPostProcessSettings& S = Air->Settings;

	// WHAT A WORLD MAY DIFFER ON. This actor is unbound and at priority ten,
	// so everything it overrides beats the level's own volume -- which means
	// the level is the WRONG place to tune any of it, and finding that out
	// cost an afternoon of writing numbers that were being ignored.
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);

	// ---- EXPOSURE ----
	S.bOverride_AutoExposureMethod = true;
	S.AutoExposureMethod = AEM_Histogram;
	S.bOverride_AutoExposureMinBrightness = true;
	S.bOverride_AutoExposureMaxBrightness = true;
	if (Wardrobe && Wardrobe->ExposureAt >= 0.f)
	{
		// PINNED. Minimum equal to maximum is an exposure that does not move,
		// so the sun going down is the only thing that darkens the picture.
		S.AutoExposureMinBrightness = Wardrobe->ExposureAt;
		S.AutoExposureMaxBrightness = Wardrobe->ExposureAt;
	}
	else
	{
		S.AutoExposureMinBrightness = ExposureLow;
		S.AutoExposureMaxBrightness = ExposureHigh;
	}
	S.bOverride_AutoExposureSpeedUp = true;
	S.AutoExposureSpeedUp = 1.6f;          // slowly: the eye does not snap
	S.bOverride_AutoExposureSpeedDown = true;
	S.AutoExposureSpeedDown = 1.1f;

	// Local exposure keeps the inside of a doorway from going to pitch while
	// the thatch above it is in full sun -- which is exactly the shot this
	// world keeps producing now the doors are cut.
	S.bOverride_LocalExposureHighlightContrastScale = true;
	S.LocalExposureHighlightContrastScale = 0.82f;
	S.bOverride_LocalExposureShadowContrastScale = true;
	S.LocalExposureShadowContrastScale = ShadowLift;

	// ---- WHAT LIGHT DOES ON THE WAY IN ----
	S.bOverride_BloomIntensity = true;
	S.BloomIntensity = Bloom;
	S.bOverride_BloomThreshold = true;
	S.BloomThreshold = 0.9f;

	S.bOverride_AmbientOcclusionIntensity = true;
	S.AmbientOcclusionIntensity = Wardrobe ? Wardrobe->Occlusion : 0.62f;
	S.bOverride_AmbientOcclusionRadius = true;
	S.AmbientOcclusionRadius = 72.f;

	// ---- THE GRADE ----
	// Filmic, and gentle. A world that is going to be looked at for hours
	// should not be shouting.
	// The slope is the contrast, and it comes from the look now; see the note
	// beside `FilmContrast`. 0.92 was chosen when the ambient was flat white,
	// and a gentle curve on top of flat light is how a picture ends up with
	// nothing in the corners of its histogram.
	S.bOverride_FilmSlope = true;
	S.FilmSlope = Wardrobe ? Wardrobe->FilmContrast : 1.04f;
	// THE DARK END OF THE CURVE. At the old 0.62 a surface in shadow landed on
	// the flat of the tone curve and came out black -- a palisade's north face,
	// a canopy's far side, the ground under a wall.
	S.bOverride_FilmToe = true;
	S.FilmToe = Wardrobe ? Wardrobe->FilmToe : 0.40f;
	S.bOverride_FilmShoulder = true;   S.FilmShoulder = 0.30f;

	S.bOverride_ColorGain = true;      S.ColorGain = FVector4(1.f, 1.f, 1.f, 1.02f);
	S.bOverride_ColorSaturation = true;
	S.ColorSaturation = FVector4(1.f, 1.f, 1.f,
		Wardrobe ? Wardrobe->FilmColour : 1.04f);
	// ---- AND WHAT THE LIGHT IS CALLED WHITE ----
	//
	// There was no white balance here at all, so the picture sat at the
	// tonemapper's own neutral: 6500K, noon under a clear sky. This world is
	// thatch, timber, cut stone and firelight, and it was reading cold. See
	// `FilmWarmth` -- above 6500 warms the image, which is the way round that
	// always surprises.
	S.bOverride_WhiteTemp = true;
	S.WhiteTemp = Wardrobe ? Wardrobe->FilmWarmth : 6500.f;

	S.bOverride_ColorGainShadows = true;
	S.ColorGainShadows = FVector4(ShadowTint.R, ShadowTint.G, ShadowTint.B, 1.f);
	S.bOverride_ColorGainHighlights = true;
	S.ColorGainHighlights = FVector4(HighlightTint.R, HighlightTint.G, HighlightTint.B, 1.f);

	S.bOverride_VignetteIntensity = true;
	S.VignetteIntensity = Vignette;
	S.bOverride_FilmGrainIntensity = true;
	S.FilmGrainIntensity = Grain;
	S.bOverride_FilmGrainIntensityShadows = true;
	S.FilmGrainIntensityShadows = Grain * 1.6f;

	// ---- SHARPNESS ----
	// Temporal upscaling is doing the anti-aliasing; without a little sharpen
	// the thatch courses and the timber frame smear into mush at any distance,
	// and those two are most of what says this is a place and not a model.
	S.bOverride_Sharpen = true;
	S.Sharpen = 0.45f;
}
