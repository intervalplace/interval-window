// Copyright interval.

#include "IntervalSound.h"
#include "IntervalGate.h"
#include "EngineUtils.h"

#include "Components/AudioComponent.h"
#include "EngineUtils.h"
#include "IntervalBridgeSubsystem.h"
#include "IntervalGround.h"
#include "IntervalLook.h"
#include "IntervalTypes.h"
#include "Sound/SoundBase.h"
#include "IntervalGeometry.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

AIntervalSound::AIntervalSound()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	auto Make = [&](const TCHAR* Name)
	{
		UAudioComponent* C = CreateDefaultSubobject<UAudioComponent>(Name);
		C->SetupAttachment(RootComponent);
		// NOT spatialised. A bed is the air a citizen is in, not a thing in
		// front of them; panning it would make the world lurch when they turn.
		C->bAllowSpatialization = false;
		C->bAutoActivate = false;
		C->bIsUISound = true;          // keeps playing while the editor is paused
		return C;
	};
	BedA = Make(TEXT("BedA"));
	BedB = Make(TEXT("BedB"));
	Piece = Make(TEXT("Piece"));
	// Rain is a bed too: it is the air a citizen is in, and panning it would
	// make the weather lurch when they turn round.
	RainOpen = Make(TEXT("RainOpen"));
	RainRoof = Make(TEXT("RainRoof"));
	Birds = Make(TEXT("Birds"));
}

UIntervalLook* AIntervalSound::Chosen() const
{
	return UIntervalLook::Resolve(Look);
}

void AIntervalSound::BeginPlay()
{
	Super::BeginPlay();

	TActorIterator<AIntervalGround> First(GetWorld());
	Ground = First ? *First : nullptr;
	if (const UGameInstance* GI = GetGameInstance())
	{
		Bridge = GI->GetSubsystem<UIntervalBridgeSubsystem>();
		if (Bridge)
		{
			Bridge->OnFrame.AddDynamic(this, &AIntervalSound::HandleFrame);
		}
	}
}

void AIntervalSound::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Bridge)
	{
		Bridge->OnFrame.RemoveDynamic(this, &AIntervalSound::HandleFrame);
	}
	Super::EndPlay(Reason);
}

void AIntervalSound::HandleFrame()
{
	// The frame is READ rather than handed over: a dynamic delegate copies
	// whatever it carries, and what this used to carry was the whole world.
	// See FIntervalFrameEvent in IntervalBridgeSubsystem.h.
	if (!Bridge) { return; }
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Ground)
	{
		TActorIterator<AIntervalGround> It(GetWorld());
		Ground = It ? *It : nullptr;
	}
	if (Ground)
	{
		// The ground the citizen is standing on, in the world's own word. Null
		// until a chunk holds that tile, which is a reason to keep the last
		// answer rather than to go silent for a frame.
		FName Word = Ground->GroundWordAtTile(Frame.Me.X, Frame.Me.Y);

		// A BANK SOUNDS LIKE WHAT IT BORDERS. See IntervalLook::BorrowsAmbience:
		// sand is a beach and a riverbank both, so the tile underfoot cannot
		// say which water is beside it and the neighbours have to.
		const UIntervalLook* Heard_ = UIntervalLook::Resolve(Look);
		if (Heard_ && !Word.IsNone() && Heard_->BorrowsAmbience.Contains(Word))
		{
			// Outward, so the nearest water wins over a further one -- a spit
			// of sand between a river and the sea should sound like whichever
			// you are standing next to.
			for (int32 Ring = 1; Ring <= 6; ++Ring)
			{
				FName Found;
				for (int32 dy = -Ring; dy <= Ring && Found.IsNone(); ++dy)
				{
					for (int32 dx = -Ring; dx <= Ring && Found.IsNone(); ++dx)
					{
						// Only the ring's edge; the inside was already asked.
						if (FMath::Max(FMath::Abs(dx), FMath::Abs(dy)) != Ring) { continue; }
						const FName Near = Ground->GroundWordAtTile(
							Frame.Me.X + dx, Frame.Me.Y + dy);
						if (Near.IsNone() || Heard_->BorrowsAmbience.Contains(Near)) { continue; }
						if (Heard_->Ambience.Contains(Near)) { Found = Near; }
					}
				}
				if (!Found.IsNone()) { Word = Found; break; }
			}
		}
		if (!Word.IsNone())
		{
			Standing = Word;
		}
	}
}

void AIntervalSound::SetBed(USoundBase* Next)
{
	UAudioComponent* In = bBedIsA ? BedB : BedA;
	if (!In || !Next)
	{
		return;
	}
	In->SetSound(Next);
	In->SetVolumeMultiplier(0.f);
	In->Play();
	bBedIsA = !bBedIsA;
	Fade = 0.f;
}

void AIntervalSound::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UIntervalLook* Look_ = Chosen();
	if (!Look_)
	{
		return;
	}

	// ---- RAIN, WHICH DOES NOT WAIT TO BE SETTLED ----
	//
	// Everything below this is about a COUNTRY -- a thing you arrive in, that
	// wants a settling time and a cross-fade. Weather is not that. It is
	// falling or it is not, and the only thing between it and your ears is a
	// roof, so it is handled first and separately, before the early-out that
	// keeps the beds quiet until the ground under the citizen is known.
	{
		if (!Weathers)
		{
			Weathers = LoadObject<UMaterialParameterCollection>(
				nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky"));
		}
		// READ, not reckoned. The hour already decided how hard it is raining,
		// including any override a level has set for looking at something, and
		// wrote it where every material reads it. Working it out again here
		// would agree until one of the two was edited.
		const float Falling = Weathers
			? FMath::Clamp(UKismetMaterialLibrary::GetScalarParameterValue(
				this, Weathers, TEXT("Rain")), 0.f, 1.f) : 0.f;

		// UNDER A ROOF. The same question the rain curtain asks, and the same
		// answer: the window worked out which tiles a building covers when it
		// built the walls. Chased rather than switched, because a doorway is
		// one tile wide and stepping across it should not cut the weather off
		// like a light.
		//
		// §7dq: AND A CAVE IS COVER, WHICH THIS DID NOT KNOW. `BuildingKeyAtTile`
		// answers for a BUILT structure, and the Smother is a hole in a
		// hillside, so standing in the dark under a hundred feet of rock the
		// window had rain falling on you and songbirds singing over you. Both
		// came through the same boolean and neither was visible as a bug from
		// the code: the roof test was correct about roofs and nobody had asked
		// it about caves. The frame already carries the surface underfoot for
		// the cave lamp, so this is the same fact read once more.
		bool bUnder = false;
		if (Ground && Bridge && Bridge->GetFrame().bHasMe)
		{
			const FIntervalEntity& Me = Bridge->GetFrame().Me;
			bUnder = Ground->BuildingKeyAtTile(Me.X, Me.Y) != 0
				|| Bridge->GetFrame().Surface.Equals(TEXT("cave"), ESearchCase::IgnoreCase);
		}
		Indoors = FMath::FInterpTo(Indoors, bUnder ? 1.f : 0.f, DeltaSeconds, 2.4f);

		auto Weather = [&](UAudioComponent* C, USoundBase* S, float Share)
		{
			if (!C) { return; }
			const float Want = Falling * Share * Look_->RainVolume;
			if (Want > 0.004f)
			{
				if (S && C->Sound != S) { C->SetSound(S); }
				if (C->Sound && !C->IsPlaying()) { C->Play(); }
				C->SetVolumeMultiplier(Want);
			}
			else if (C->IsPlaying())
			{
				C->Stop();
			}
		};
		Weather(RainOpen, Look_->RainSound, 1.f - Indoors);
		Weather(RainRoof, Look_->RainRoofSound, Indoors);

		// ---- BIRDS, WHICH ARE A KIND OF WEATHER TOO ----
		//
		// Same seam as the rain and for the same reason: this is about the
		// sky and the roof, not about which country the citizen is standing
		// in, so it must not wait on the beds' settling time.
		//
		// Three gates, all of them things the ear checks. Day, because
		// birdsong at midnight is uncanny in a way nobody has to be told to
		// notice. Out from under a roof, chased not switched, so a doorway
		// fades rather than clicks. And silence in rain -- the one that
		// matters most, because a track that chirps through a downpour is
		// worse than no track: it is actively wrong, and the ear hears the
		// lie even when the eye has not looked up.
		if (Birds)
		{
			const float Daylight = Weathers
				? FMath::Clamp(UKismetMaterialLibrary::GetScalarParameterValue(
					this, Weathers, TEXT("Day")), 0.f, 1.f) : 0.f;

			// ---- AND WHICH CREATURE, WHICH IS A FACT ABOUT THE GROUND ----
			//
			// One birdsong was playing everywhere: over the moor, over the
			// shingle, over the peat. That is the audio version of one mesh
			// standing in for every prop, and it was reported as such --
			// "sound of crows in moor instead of regular bird song". The
			// window already knows which country the ground underfoot is;
			// `GroundVoices` is that answer, and `BirdSound` is what a word
			// with no row of its own falls back to.
			USoundBase* Voice = Look_->BirdSound;
			if (const TObjectPtr<USoundBase>* Local = Look_->GroundVoices.Find(Standing))
			{
				if (*Local) { Voice = Local->Get(); }
			}

			// ---- AND NOT EVERY CREATURE KEEPS A SONGBIRD'S HOURS ----
			//
			// The gates below were written for songbirds and are right for
			// them: silent at night, silent in rain, silent under a roof. Two
			// of the three are simply wrong for anything else. Crows call in
			// foul weather -- a wet moor is when you hear them most -- and
			// frogs are a DUSK animal that a daylight gate would silence at
			// exactly the hour the fens are loudest, and that rain makes
			// louder rather than quieter.
			//
			// Read off the voice rather than off a table, because the alter-
			// native is a second table saying the same thing twice.
			const FString Named = Voice ? Voice->GetName() : FString();
			const bool bCrows = Named.Contains(TEXT("crow"));
			const bool bGulls = Named.Contains(TEXT("gull"));
			const bool bFrogs = Named.Contains(TEXT("frog"));

			// Squared for a songbird: dawn and dusk should be thin rather
			// than half-loud, and they should be gone well before the light
			// is. Crows and gulls keep a longer day. Frogs are the other way
			// round entirely and come up as the light goes.
			float Hour = Daylight * Daylight;
			if (bCrows || bGulls) { Hour = FMath::Sqrt(Daylight) * 0.85f + 0.15f; }
			if (bFrogs) { Hour = 0.35f + 0.65f * (1.f - Daylight); }

			const float Wet = FMath::Clamp(Falling * 1.6f, 0.f, 1.f);
			float Weatherly = 1.f - Wet;
			if (bCrows || bGulls) { Weatherly = 1.f - Wet * 0.25f; }
			if (bFrogs) { Weatherly = 1.f + Wet * 0.45f; }

			const float Want = Hour * (1.f - Indoors) * Weatherly * Look_->BirdVolume;
			if (Want > 0.004f)
			{
				// CHANGED, NOT CROSS-FADED, and that is on purpose. These are
				// mostly silence by construction -- a call every few seconds
				// with nothing between -- so a swap lands in a gap almost
				// every time, and two of them overlapping would be two flocks.
				if (Voice && Birds->Sound != Voice)
				{
					Birds->SetSound(Voice);
					Birds->Play();
				}
				if (Birds->Sound && !Birds->IsPlaying()) { Birds->Play(); }
				Birds->SetVolumeMultiplier(Want);
			}
			else if (Birds->IsPlaying())
			{
				Birds->Stop();
			}
		}
	}

	// ---- §6c: AND EVERYTHING DUCKS WHEN THE CITIZEN GOES DOWN ----
	//
	// A death has to be heard as well as seen. The screen washes over and the
	// one noise left is the fall itself, which is the whole of what "a clear
	// break" means to an ear: the world you were standing in stops being
	// audible for a moment.
	//
	// DUCKED AND NOT STOPPED, which matters now that a piece plays once a
	// session. Stopping the music would mark it spent for a death, and a
	// citizen would lose the country's only piece to a goblin. Dipped, it is
	// still running underneath and comes back up where it was.
	{
		int32 Hp = 1;
		bool bHaveMe = false;
		if (Bridge && Bridge->GetFrame().bHasMe)
		{
			bHaveMe = true;
			if (const FString* Told = Bridge->GetFrame().Me.Fields.Find(TEXT("health")))
			{
				Hp = FCString::Atoi(**Told);
			}
		}
		const bool bDown = bHaveMe && Hp <= 0;
		// The same pace as the wash over the screen, so the two read as one
		// thing happening. See UIntervalHudWidget::FillDeath.
		Grief = FMath::Clamp(Grief + DeltaSeconds / (bDown ? 0.5f : -0.28f), 0.f, 1.f);
	}
	const float Hush = 1.f - Grief * 0.88f;

	if (Standing.IsNone())
	{
		return;
	}

	// ---- HAS THIS STAY BEEN DECIDED? ----
	// A boundary is a line a citizen can stand astride. Without a settling
	// time, shifting your weight starts and stops a theme.
	if (Standing != Settled)
	{
		StandingFor += DeltaSeconds;
		if (StandingFor >= SettleSeconds)
		{
			// LEAVING A COUNTRY DOES NOT MAKE ITS PIECE HEARABLE AGAIN.
			//
			// This used to clear the country from `Heard` on the way out,
			// which made the rule once per VISIT. Asked for once per session
			// instead, and the reason is the right one: "for scarcity so that
			// the tracks are more memorable/emotionally meaningful". A piece
			// you have heard four times in an hour is furniture.
			//
			// The world does not go quiet when they are spent. The ambience
			// bed below is a separate thing and is never gated -- the birds
			// for the biome, frogs in the fens, wind, water and rain all keep
			// going, so what is left when the music has been spent is the
			// place's own sound rather than silence.
			Settled = Standing;
			StandingFor = 0.f;

			if (const TObjectPtr<USoundBase>* Bed = Look_->Ambience.Find(Settled))
			{
				SetBed(Bed->Get());
				UE_LOG(LogTemp, Log, TEXT("interval: standing on %s"), *Settled.ToString());
			}

		}
	}
	else
	{
		StandingFor = 0.f;
	}

	// ---- THE COUNTRY'S OWN PIECE, ONCE THE DOOR IS OPEN ----
	//
	// This used to live inside the branch that runs the moment a stay is
	// settled, which is exactly once per arrival. That was fine until the
	// window grew a gate: the theme at the title card and the country's piece
	// played over each other, two pieces of music at a time, until the theme
	// faded on the way in and left the other one running underneath -- "at
	// the gate, before entering, only the theme should play".
	//
	// Skipping the play inside that branch would not have been enough. The
	// branch fires once, so a country skipped at the gate would never be
	// played at all, and a citizen would walk into a world that had silently
	// spent the one piece written for the ground they were standing on. So
	// the decision moved OUT here, where it is asked every tick: play the
	// settled country's piece when the door is open, nothing is already
	// playing, and this country's piece has not been heard this session.
	//
	// The ambience bed is deliberately NOT held back. Wind and water under a
	// title card is not a second piece of music; it is the world being
	// audible behind the door, which is the point of the shot.
	if (!Settled.IsNone())
	{
		// WHICH PIECE BELONGS TO THIS GROUND, and whether it has been heard.
		//
		// Asked FIRST, and cheaply, because of what this block became: while
		// a piece was cleared on leaving a country there was always one to
		// play, and now there is not. Once the nine are spent this test is
		// all that runs for the rest of the session -- a map lookup and a set
		// lookup -- where finding the gate means walking the level's actors,
		// every tick, for nothing.
		const TObjectPtr<USoundBase>* Track = Look_->Music.Find(Settled);
		USoundBase* Piece_ = Track ? Track->Get() : nullptr;
		// Nine pieces cover thirty surface words, so the ground a citizen is
		// standing on does not identify the music written for it. See `Heard`.
		if (Piece_ && !Heard.Contains(Piece_->GetFName()))
		{
			TActorIterator<AIntervalGate> Doors(GetWorld());
			const AIntervalGate* Door = Doors ? *Doors : nullptr;
			// A piece with somewhere to get to is allowed to get there.
			const bool bBusy = Piece && Piece->IsPlaying();
			if (!(Door && Door->IsWaiting()) && !bBusy)
			{
				Heard.Add(Piece_->GetFName());
				Piece->SetSound(Piece_);
				Piece->SetVolumeMultiplier(MusicVolume * Hush);
				Piece->Play();
				UE_LOG(LogTemp, Log,
					TEXT("interval: the %s, heard (%d of the pieces spent)"),
					*Settled.ToString(), Heard.Num());
			}
		}
	}

	// ---- THE CROSS-FADE ----
	if (Fade < 1.f)
	{
		Fade = FMath::Min(1.f, Fade + DeltaSeconds / FMath::Max(0.1f, CrossFade));
		UAudioComponent* In = bBedIsA ? BedA : BedB;
		UAudioComponent* Out = bBedIsA ? BedB : BedA;
		if (In) { In->SetVolumeMultiplier(AmbienceVolume * Fade * Hush); }
		if (Out)
		{
			Out->SetVolumeMultiplier(AmbienceVolume * (1.f - Fade) * Hush);
			if (Fade >= 1.f) { Out->Stop(); }
		}
	}
}
