#include "IntervalCitizens.h"
#include "IntervalGate.h"
#include "IntervalAnim.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalGeometry.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "IntervalLook.h"
#include "NiagaraFunctionLibrary.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/WidgetComponent.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "Blueprint/WidgetTree.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "IntervalGround.h"
#include "EngineUtils.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalCitizens, Log, All);

TSharedRef<SWidget> UIntervalPlateWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// ---- A NAME AND A DEED ARE TWO DIFFERENT KINDS OF FACT ----
		//
		// They were one text block with a newline in it, so "gather" was drawn
		// in exactly the hand that says who somebody is -- same size, same
		// weight, same colour -- and read as part of their title. It is not:
		// a name is what you are and is there always, a deed is what you are
		// doing THIS SECOND and will be gone in a moment. Smaller, gold and
		// set apart says that without anybody having to work it out.
		UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());
		Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Label"));
		Label->SetJustification(ETextJustify::Center);
		Stack->AddChildToVerticalBox(Label);

		Deed = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Deed"));
		Deed->SetJustification(ETextJustify::Center);
		Deed->SetColorAndOpacity(FSlateColor(FLinearColor(0.839f, 0.659f, 0.290f, 1.f)));
		Deed->SetVisibility(ESlateVisibility::Collapsed);
		Stack->AddChildToVerticalBox(Deed);
		WidgetTree->RootWidget = Stack;
	}
	return Super::RebuildWidget();
}

TSharedRef<SWidget> UIntervalSplatWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// ONE FIGURE AND NOTHING BEHIND IT. The plate and the bubble both sit
		// on an ink board, because both are things to be READ and a board is
		// what makes a line of text legible over grass. A splat is not read,
		// it is GLANCED at: it wants to be gone before the eye finishes with
		// it, and a board would make a solid rectangle flashing over every
		// blow in a fight.
		Figure = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Figure"));
		Figure->SetJustification(ETextJustify::Center);
		WidgetTree->RootWidget = Figure;
	}
	return Super::RebuildWidget();
}

void UIntervalSplatWidget::Show(int32 Amount, const FLinearColor& Tint, float Through)
{
	if (!Figure)
	{
		return;
	}
	// A BLOW THAT MISSED IS NOT A BLANK. The world reports a zero in a flurry's
	// blow list for a swing that found nothing, and `window-web` shows it,
	// because four blows of which two landed is a different thing from two
	// blows and the difference is the whole texture of a flurry.
	Figure->SetText(FText::FromString(Amount > 0 ? FString::FromInt(Amount) : TEXT("-")));

	// Up, and out. Fading on a curve rather than linearly so it is fully
	// legible for most of its life and then goes quickly, instead of spending
	// the whole second as a smear nobody can read.
	const float Fade = FMath::Clamp(1.f - FMath::Pow(Through, 2.2f), 0.f, 1.f);
	FLinearColor C = Tint;
	C.A = Fade;
	Figure->SetColorAndOpacity(FSlateColor(C));

	FSlateFontInfo Font = Figure->GetFont();
	Font.Size = Amount > 0 ? 17 : 13;
	Font.TypefaceFontName = TEXT("Regular");
	Figure->SetFont(Font);
	Figure->SetRenderOpacity(Fade);
}

TSharedRef<SWidget> UIntervalBubbleWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		// The same two borders the interface panels are made of -- a gold rule
		// round a board of ink -- so a line over a head and the same line in
		// the chat log are visibly one thing.
		Edge = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Edge->SetPadding(FMargin(2.f));
		Edge->Background.DrawAs = ESlateBrushDrawType::RoundedBox;
		Edge->Background.OutlineSettings.CornerRadii = FVector4(7.f, 7.f, 7.f, 7.f);
		Edge->Background.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;

		FaceOf = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		FaceOf->SetPadding(FMargin(9.f, 4.f, 9.f, 5.f));
		FaceOf->Background.DrawAs = ESlateBrushDrawType::RoundedBox;
		FaceOf->Background.OutlineSettings.CornerRadii = FVector4(6.f, 6.f, 6.f, 6.f);
		FaceOf->Background.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
		FaceOf->Background.TintColor = FSlateColor(FLinearColor(0.038f, 0.040f, 0.052f, 0.93f));
		FaceOf->SetBrushColor(FLinearColor(0.038f, 0.040f, 0.052f, 0.93f));

		Line = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Line->SetJustification(ETextJustify::Center);
		Line->SetAutoWrapText(true);
		Line->SetWrapTextAt(300.f);
		FSlateFontInfo Font = Line->GetFont();
		Font.Size = 13;
		Line->SetFont(Font);

		FaceOf->AddChild(Line);
		Edge->AddChild(FaceOf);

		// ---- IT HAS TO HUG THE WORDS ----
		//
		// A widget component draws its widget at a FIXED size, and a border
		// made the root stretches to fill it -- so three words got the same
		// wide slab as a whole sentence, and the slab was wide enough to cover
		// the name plate underneath. An overlay slot aligned centre lets the
		// child take its own desired size instead, so the plate is as wide as
		// what is written on it and no wider.
		UOverlay* Middle = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		if (UOverlaySlot* Fit = Cast<UOverlaySlot>(Middle->AddChild(Edge)))
		{
			Fit->SetHorizontalAlignment(HAlign_Center);
			Fit->SetVerticalAlignment(VAlign_Bottom);
		}
		WidgetTree->RootWidget = Middle;
	}
	return Super::RebuildWidget();
}

void UIntervalBubbleWidget::Set(const FString& Text, bool bFar)
{
	if (!Line || !Edge)
	{
		return;
	}
	Line->SetText(FText::FromString(Text));
	// THE CHANNEL IS IN THE RULE ROUND IT. A word to the island is gold; a
	// word to the people beside you is the quieter grey. Nobody has to read a
	// tag to know which they are looking at.
	const FLinearColor Band = bFar
		? FLinearColor(0.839f, 0.659f, 0.290f, 0.92f)
		: FLinearColor(0.42f, 0.44f, 0.50f, 0.85f);
	Edge->Background.TintColor = FSlateColor(Band);
	Edge->SetBrushColor(Band);
	Line->SetColorAndOpacity(FSlateColor(bFar
		? FLinearColor(0.97f, 0.91f, 0.76f, 1.f)
		: FLinearColor(0.90f, 0.89f, 0.84f, 1.f)));
}

void UIntervalPlateWidget::Doing(const FString& Text, float Size, bool bCrowed)
{
	if (!Deed)
	{
		return;
	}
	if (Text.IsEmpty())
	{
		Deed->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	Deed->SetVisibility(ESlateVisibility::HitTestInvisible);
	Deed->SetText(FText::FromString(Text));
	FSlateFontInfo Font = Deed->GetFont();
	// UPRIGHT AND FULL SIZE FOR AN EVENT, smaller and italic for a state.
	// The line is the same line either way: a second widget over one head is
	// a heads-up display, which this plate exists not to be.
	Font.Size = FMath::Max(static_cast<int32>(Size) - (bCrowed ? 0 : 2), 1);
	Font.TypefaceFontName = bCrowed ? TEXT("Regular") : TEXT("Italic");
	Deed->SetFont(Font);
}

void UIntervalPlateWidget::Set(const FString& Text, const FLinearColor& Colour, float Size)
{
	if (!Label)
	{
		return;
	}
	Label->SetText(FText::FromString(Text));
	Label->SetColorAndOpacity(FSlateColor(Colour));
	FSlateFontInfo Font = Label->GetFont();
	Font.Size = FMath::Max(static_cast<int32>(Size), 1);
	Label->SetFont(Font);
}

void AIntervalCitizens::Overheard(const FIntervalSaid& Said)
{
	// A bubble is made ON FIRST SPEECH and never for silence: a market square
	// with forty people in it should not cost forty widgets nobody reads.
	FIntervalCitizenView* View = Citizens.Find(Said.SpeakerId);
	if (!View)
	{
		return;
	}
	if (!View->Bubble)
	{
		UWidgetComponent* Made = NewObject<UWidgetComponent>(this);
		Made->SetupAttachment(RootComponent);
		Made->SetMobility(EComponentMobility::Movable);
		Made->SetWidgetSpace(EWidgetSpace::Screen);
		Made->SetWidgetClass(UIntervalBubbleWidget::StaticClass());
		Made->SetDrawSize(FVector2D(340.f, 56.f));
		Made->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Made->RegisterComponent();
		View->Bubble = Made;
	}
	View->Spoken = Said.Text;
	View->bSpokenFar = Said.Scope == TEXT("far");
	View->bSpokenShown = false;
	View->Bubble->SetVisibility(true);
	View->BubbleUntil = FPlatformTime::Seconds() + BubbleSeconds;
}

// ---------- §7ca: THE NUMBERS OVER A FIGHT ----------
//
// SIX BLOWS, SIX SPLATS. A splat is made by diffing hitpoints between two
// intervals, so a flurry of six came out of the arithmetic as a single number
// and a citizen could not tell a lucky burst from an even one. The engine
// reports each blow in `blows`, so each blow is shown: fanned about the body
// and staggered a few milliseconds apart so they read as a burst rather than
// as a stack.
//
// ONLY WHEN THE LIST ACCOUNTS FOR THE WHOLE DROP. If the blow list and the
// hitpoint difference disagree, the difference is the truth and the fan is a
// guess, so it falls back to the single honest number. `window-web` has made
// exactly this judgement since §7ca and the two windows must not disagree
// about what a fight looked like.
//
// Arrays are not flattened into dotted fields, so `blows` arrives here as the
// condensed JSON the bridge sent: `[3,0,5]`. It is parsed rather than
// forwarded in some friendlier shape, because the friendlier shape would be a
// second definition of the same fact.
void AIntervalCitizens::Splat(const FVector& Where, int32 Amount, float Fan,
	float Delay, bool bOnMe)
{
	if (!bShowSplats)
	{
		return;
	}
	// The oldest goes rather than the newest being refused: in a battle the
	// number that just landed is the one somebody is looking for.
	while (Splats.Num() >= FMath::Max(SplatsAtOnce, 1))
	{
		if (Splats[0].Widget)
		{
			Splats[0].Widget->SetVisibility(false);
			SpareSplats.Add(Splats[0].Widget);
		}
		Splats.RemoveAt(0);
	}

	UWidgetComponent* W = nullptr;
	if (SpareSplats.Num() > 0)
	{
		W = SpareSplats.Pop();
	}
	else
	{
		W = NewObject<UWidgetComponent>(this);
		W->SetupAttachment(RootComponent);
		W->SetMobility(EComponentMobility::Movable);
		W->SetWidgetSpace(EWidgetSpace::Screen);
		W->SetWidgetClass(UIntervalSplatWidget::StaticClass());
		W->SetDrawSize(FVector2D(90.f, 34.f));
		W->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		W->RegisterComponent();
	}
	if (!W)
	{
		return;
	}
	W->SetWorldLocation(Where + FVector(0.f, 0.f, SplatHeight));
	// Hidden until its moment: a staggered blow that drew on the interval it
	// was queued would land all six at once, which is the thing the stagger
	// exists to prevent.
	W->SetVisibility(Delay <= 0.f);

	FIntervalSplat S;
	S.Widget = W;
	S.Origin = Where;
	S.At = FPlatformTime::Seconds();
	S.Delay = Delay;
	S.Fan = Fan;
	S.Amount = Amount;
	S.bOnMe = bOnMe;
	Splats.Add(S);
}

void AIntervalCitizens::SplatsFor(FIntervalCitizenView& View, const FIntervalEntity& Body,
	const FVector& Where, bool bOnMe)
{
	if (!bShowSplats)
	{
		return;
	}
	int32 Hp = 0;
	if (const FString* Told = Body.Fields.Find(TEXT("health")))
	{
		Hp = FCString::Atoi(**Told);
	}

	const int32 Was = View.LastHp;
	View.LastHp = Hp;
	// A body seen for the first time has taken nothing as far as this window
	// knows, and the dead take no more.
	if (Was < 0 || Hp >= Was || Hp < 0)
	{
		return;
	}
	const int32 Drop = Was - Hp;

	// The blow list, if the world sent one. Condensed JSON, as all arrays are.
	TArray<int32> Blows;
	if (const FString* Told = Body.Fields.Find(TEXT("blows")))
	{
		FString Raw = *Told;
		Raw.ReplaceInline(TEXT("["), TEXT(""));
		Raw.ReplaceInline(TEXT("]"), TEXT(""));
		TArray<FString> Parts;
		Raw.ParseIntoArray(Parts, TEXT(","), true);
		for (const FString& Part : Parts)
		{
			Blows.Add(FCString::Atoi(*Part.TrimStartAndEnd()));
		}
	}
	int32 Sum = 0;
	for (int32 B : Blows)
	{
		Sum += B;
	}

	if (Blows.Num() > 1 && Sum == Drop)
	{
		for (int32 i = 0; i < Blows.Num(); ++i)
		{
			const float Fan = (static_cast<float>(i) - (Blows.Num() - 1) * 0.5f) * SplatFan;
			Splat(Where, Blows[i], Fan, i * SplatStagger, bOnMe);
		}
		return;
	}
	Splat(Where, Drop, 0.f, 0.f, bOnMe);
}

void AIntervalCitizens::DriveSplats()
{
	const double Now = FPlatformTime::Seconds();
	const float Life = FMath::Max(SplatSeconds, 0.05f);
	for (int32 i = Splats.Num() - 1; i >= 0; --i)
	{
		FIntervalSplat& S = Splats[i];
		const float Age = static_cast<float>(Now - S.At) - S.Delay;
		if (Age < 0.f)
		{
			continue;                       // still waiting its turn in the burst
		}
		if (Age >= Life || !S.Widget)
		{
			if (S.Widget)
			{
				S.Widget->SetVisibility(false);
				SpareSplats.Add(S.Widget);
			}
			Splats.RemoveAt(i);
			continue;
		}
		const float Through = Age / Life;
		S.Widget->SetVisibility(true);
		// Rising, and easing as it goes: a number that climbs at a constant
		// rate for a whole second reads as a thing being moved rather than a
		// thing thrown.
		const float Up = SplatRise * FMath::Sqrt(Through);
		S.Widget->SetWorldLocation(S.Origin + FVector(S.Fan, 0.f, SplatHeight + Up));
		if (UIntervalSplatWidget* Face = Cast<UIntervalSplatWidget>(S.Widget->GetUserWidgetObject()))
		{
			// WHOSE BLOOD IT IS. A number coming off the citizen being played
			// is the one that matters most and is the one easiest to miss in a
			// crowd, so it is told apart by colour rather than by position.
			Face->Show(S.Amount,
				S.bOnMe ? FLinearColor(0.94f, 0.33f, 0.28f, 1.f)
				        : FLinearColor(0.96f, 0.93f, 0.86f, 1.f),
				Through);
		}
	}
}

AIntervalCitizens::AIntervalCitizens()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AIntervalCitizens::BeginPlay()
{
	Super::BeginPlay();

	UGameInstance* GameInstance = GetGameInstance();
	Bridge = GameInstance ? GameInstance->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	if (!Bridge)
	{
		UE_LOG(LogIntervalCitizens, Error, TEXT("no bridge subsystem: is the plugin enabled?"));
		return;
	}
	Bridge->OnFrame.AddDynamic(this, &AIntervalCitizens::HandleFrame);
	Bridge->OnChat.AddDynamic(this, &AIntervalCitizens::Overheard);

	// ---- AND THE MANNEQUIN NOBODY EVER MEANT TO DRAW ----
	//
	// The pawn is a CAMERA, not a person. This window builds every citizen --
	// the player's own included -- out of the frame the bridge sends, and
	// stands them where the world says; the pawn exists so that Unreal has
	// something to hang a camera and an input mode off, and its body should
	// never appear.
	//
	// It appeared. The project was started from the TopDown template, whose
	// character blueprint carries Epic's own `SKM_Manny_Simple`, and that
	// mannequin was drawn ninety-five centimetres under every citizen for as
	// long as this window has existed. From a top-down camera it reads as a
	// pale figure crouched at their feet, which is how it was reported from
	// the stream: "looks like it's standing on the shoulders of a mannequin".
	//
	// It survived every audit because no table in this project names it: the
	// art audit walks the tables, and a mesh nothing names is a mesh nothing
	// checks. Hidden rather than deleted, because the pawn's mesh component
	// is also what its movement component is sized against.
	// NOT HERE, THOUGH. This actor's BeginPlay runs before the pawn is
	// possessed, so `GetPlayerPawn` answers null and the hide is a no-op that
	// reports nothing. It is done on the first frame instead -- see
	// HideTheCameraBody, called from HandleFrame.
}

void AIntervalCitizens::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Bridge)
	{
		Bridge->OnFrame.RemoveDynamic(this, &AIntervalCitizens::HandleFrame);
		Bridge->OnChat.RemoveDynamic(this, &AIntervalCitizens::Overheard);
	}
	Super::EndPlay(EndPlayReason);
}

FName AIntervalCitizens::MobKey(const FIntervalEntity& Mob) const
{
	if (const FString* Face = Mob.Fields.Find(TEXT("face")))
	{
		if (!Face->IsEmpty())
		{
			const FName Special(*(Mob.Kind + TEXT(".") + *Face));
			if (Mobs.Contains(Special))
			{
				return Special;
			}
		}
	}
	return FName(*Mob.Kind);
}

void AIntervalCitizens::HideTheCameraBody()
{
	// Cheap enough to ask every frame and it answers once: the world ticks
	// once a second, and the moment the pawn exists this is done for good.
	if (bCameraBodyHidden) { return; }
	APawn* Camera = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Camera) { return; }
	TArray<USkeletalMeshComponent*> Bodies;
	Camera->GetComponents<USkeletalMeshComponent>(Bodies);
	for (USkeletalMeshComponent* Body : Bodies)
	{
		Body->SetVisibility(false, true);
		Body->SetCastShadow(false);
	}
	bCameraBodyHidden = true;
	UE_LOG(LogIntervalCitizens, Log,
		TEXT("the camera's own body is hidden (%d component(s))"), Bodies.Num());
}

void AIntervalCitizens::HandleFrame()
{
	// The frame is READ rather than handed over: a dynamic delegate copies
	// whatever it carries, and what this used to carry was the whole world.
	// See FIntervalFrameEvent in IntervalBridgeSubsystem.h.
	if (!Bridge) { return; }
	const FIntervalFrame& Frame = Bridge->GetFrame();
	// §7dn/§7dq: where the one gap in reach is, if there is one. See VerbFor.
	ThresholdTileX = Frame.ThresholdX;
	ThresholdTileY = Frame.ThresholdY;
	HideTheCameraBody();
	// The cast list, not the positions. Instance arrays are rebuilt only when
	// somebody joins, dies or walks out of view; the seven hundred transforms
	// are written every rendered frame instead, which is cheap, while adding
	// and removing instances is not.
	uint64 Digest = static_cast<uint64>(Frame.Mobs.Num()) * 1099511628211ull;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Mobs)
	{
		// THE FACE COUNTS TOWARDS THE CAST. Two incursions of the same type and
		// different faces are two different pools, and a digest that only sees
		// `type` would never notice the second one arriving.
		Digest ^= GetTypeHash(Pair.Key) * 31u + GetTypeHash(MobKey(Pair.Value));
	}
	if (Digest == LastCastDigest)
	{
		return;
	}
	LastCastDigest = Digest;

	BeastOrder.Reset();
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Mobs)
	{
		const FIntervalEntity& Mob = Pair.Value;
		if (Mob.Kind.IsEmpty())
		{
			continue;
		}
		const FName Key = MobKey(Mob);
		const FIntervalPropKind* Kind = Bestiary().Find(Key);
		if (Kind && Kind->Skeletal)
		{
			continue;   // drawn as a skeleton instead; see UpdateBeasts
		}
		if (!Kind || !Kind->Mesh)
		{
			if (!Reported.Contains(Key))
			{
				Reported.Add(Key);
				UE_LOG(LogIntervalCitizens, Warning,
					TEXT("the world says a '%s' is out there and this window has no mesh for it"),
					*Key.ToString());
			}
			continue;
		}
		BeastOrder.FindOrAdd(Key).Add(Pair.Key);
	}

	// Resize each pool once, here, to match its cast.
	for (const TPair<FName, TArray<FString>>& Pair : BeastOrder)
	{
		const FIntervalPropKind* Kind = Bestiary().Find(Pair.Key);
		TObjectPtr<UInstancedStaticMeshComponent>* Found = BeastPools.Find(Pair.Key);
		UInstancedStaticMeshComponent* Pool = Found ? Found->Get() : nullptr;
		if (!Pool)
		{
			Pool = NewObject<UInstancedStaticMeshComponent>(this);
			Pool->SetupAttachment(RootComponent);
			Pool->SetMobility(EComponentMobility::Movable);
			Pool->SetStaticMesh(Kind->Mesh);
			Pool->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Pool->RegisterComponent();
			// After registration, or the override is dropped and every beast
			// wears the engine's checkered default. See IntervalStructures.cpp.
			if (Kind->Material)
			{
				Pool->SetMaterial(0, Kind->Material);
			}
			Pool->SetCastShadow(Kind->bCastShadow);
			BeastPools.Add(Pair.Key, Pool);
		}

		const int32 Want = Pair.Value.Num();
		Pool->ClearInstances();
		for (int32 Index = 0; Index < Want; ++Index)
		{
			Pool->AddInstance(FTransform::Identity, true);
		}
	}
	// Kinds that emptied out keep their pool but lose their instances.
	for (const TPair<FName, TObjectPtr<UInstancedStaticMeshComponent>>& Pair : BeastPools)
	{
		if (!BeastOrder.Contains(Pair.Key) && Pair.Value)
		{
			Pair.Value->ClearInstances();
		}
	}
}

bool AIntervalCitizens::LastDrawnAt(const FString& Id, FVector& OutLocation) const
{
	if (const FIntervalCitizenView* View = Citizens.Find(Id))
	{
		if (View->Mesh)
		{
			OutLocation = View->Mesh->GetComponentLocation();
			return true;
		}
	}
	return false;
}

bool AIntervalCitizens::DrawnPosition(const FString& Id, const FIntervalEntity& Now,
	const TMap<FString, FIntervalEntity>& Before, float Alpha, int64 Tick,
	FVector& OutLocation, bool& bOutMoving)
{
	const FVector To = UIntervalGeometry::TileToWorld(Now.X, Now.Y);
	const FIntervalEntity* Was = Before.Find(Id);
	if (!Was)
	{
		// Newly in view: place, do not slide in from nowhere.
		FIntervalStride& Fresh = Strides.FindOrAdd(Id);
		Fresh.From = To;
		Fresh.At = To;
		Fresh.Tick = Tick;
		OutLocation = To;
		bOutMoving = false;
		return false;
	}

	bOutMoving = (Was->X != Now.X) || (Was->Y != Now.Y);

	// A JUMP IS NOT A WALK, AND WAS BEING DRAWN AS ONE.
	//
	// This lerped from the last tile to the new one whatever the distance, and
	// `GroundSpeed` below drives the animation off tiles-moved per interval. A
	// citizen stays within one tile an interval, EXCEPT twice: the ferry puts
	// them at the far quay (Eastmere to Whiting is fifty-five tiles, Fenmarch to
	// the Lists is a hundred and fifty-eight) and a death puts them at the
	// spawn, which can be four hundred. Both came out as a one-second glide
	// across open sea or open country with the walk cycle playing at a hundred
	// and fifty tiles a second.
	//
	// So it is not a teleport, it is worse: a teleport reads as a cut and this
	// read as a citizen skating. The rule the window needs is the dual of
	// "walking must never show the tick": a move the citizen could not have
	// WALKED must never be drawn as walking. One tile is a step; anything more
	// is something else happening, and it is placed, not slid.
	//
	// Diagonals count as one, because a citizen walks them.
	const int32 Leap = FMath::Max(FMath::Abs(Now.X - Was->X), FMath::Abs(Now.Y - Was->Y));
	if (Leap > 1)
	{
		FIntervalStride& Jump = Strides.FindOrAdd(Id);
		Jump.From = To;
		Jump.At = To;
		Jump.Tick = Tick;
		OutLocation = To;
		bOutMoving = false;              // and no walk cycle over the water
		return false;
	}

	FIntervalStride& Stride = Strides.FindOrAdd(Id);
	if (Stride.Tick != Tick)
	{
		// A NEW INTERVAL. This stride starts wherever the last one had got to,
		// which on a late interval is the tile they reached and on an early
		// one is somewhere short of it. Either way it is where they are being
		// drawn this instant, so nothing jumps. The first interval after they
		// appear has no drawn position yet and falls back to the told tile.
		Stride.From = (Stride.Tick == 0)
			? UIntervalGeometry::TileToWorld(Was->X, Was->Y) : Stride.At;
		Stride.Tick = Tick;
	}
	Stride.At = FMath::Lerp(Stride.From, To, Alpha);
	OutLocation = Stride.At;
	return bOutMoving;
}

void AIntervalCitizens::Footfall(const FIntervalFootfall& Fall, const FVector& At)
{
	if (Feet.Num() == 0)
	{
		for (int32 i = 0; i < 8; ++i)
		{
			UAudioComponent* Voice = NewObject<UAudioComponent>(this);
			Voice->SetupAttachment(RootComponent);
			Voice->SetMobility(EComponentMobility::Movable);
			Voice->bAutoActivate = false;
			Voice->bAllowSpatialization = true;
			Voice->bOverrideAttenuation = true;
			FSoundAttenuationSettings& Reach = Voice->AttenuationOverrides;
			Reach.bAttenuate = true;
			Reach.bSpatialize = true;
			Reach.AttenuationShape = EAttenuationShape::Sphere;
			Reach.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
			Reach.AttenuationShapeExtents = FVector(90.f, 0.f, 0.f);
			Reach.FalloffDistance = 2800.f;
			Voice->RegisterComponent();
			Feet.Add(Voice);
		}
	}
	UAudioComponent* Voice = Feet[NextFoot % Feet.Num()];
	NextFoot = (NextFoot + 1) % Feet.Num();
	if (!Voice) { return; }
	USoundBase* Which = Fall.Sounds[FMath::RandHelper(Fall.Sounds.Num())];
	if (!Which) { return; }
	Voice->SetWorldLocation(At);
	Voice->SetSound(Which);
	Voice->SetVolumeMultiplier(FMath::Max(0.f, Fall.Volume));
	// A LITTLE EITHER SIDE OF ITS OWN PITCH. Three samples is past where the
	// repeat can be heard; three samples always at the same pitch is not.
	Voice->SetPitchMultiplier(1.f + FMath::FRandRange(-Fall.PitchJitter, Fall.PitchJitter));
	Voice->Play();
}

void AIntervalCitizens::DeedHeard(const FString& Id, const FIntervalEntity& Who,
	const FName& Verb, const FVector& At, bool bOngoing, int64 Tick)
{
	// ONE DEED, ONE NOISE. The world says `deed` for the interval it is true
	// and the window draws sixty frames inside that interval, so this speaks
	// only when the word changes. A citizen who casts the same spell on two
	// consecutive intervals is heard twice, because the word goes away in
	// between: the engine drops it at the start of every interval.
	//
	// AN ACTION IS PACED INSTEAD OF LATCHED. `gather` and the two attacks are
	// one word that stays put for as long as the work lasts, so the rule above
	// gave them exactly one noise and then silence: a citizen could fell a
	// tree for ten minutes on a single thock. An action is spoken once per
	// world interval, which is the rate the blows land at anyway, so the axe
	// keeps time with the arm.
	FName& Last = LastDeed.FindOrAdd(Id);
	// Not FindOrAdd: an int64 defaults to zero and zero is a real interval at
	// a world's genesis, which would swallow the first beat of the first deed
	// ever done. The absent case has to be a tick no world can be on.
	const int64* Heard = LastDeedTick.Find(Id);
	const bool bFresh = (Last != Verb) || (bOngoing && (!Heard || *Heard != Tick));
	Last = Verb;
	LastDeedTick.Add(Id, Tick);
	if (!bFresh || Verb.IsNone()) { return; }

	// Through `Resolve`, like every other reader of the look in this file:
	// `Look` is the actor's own pointer and may be unset, in which case the
	// default asset answers.
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe) { return; }

	// ---- AND WHAT IT WAS DONE WITH ----
	//
	// The same `<verb>.<what is in the hand>` rule the motions use, and for
	// the same reason. `gambit` is one word for seven different moves: a
	// dagger's flurry, a maul's whole-body blow, a siphon going off and the
	// dragonbow's long shot. They already LOOK different, because the look
	// asset has a row for each; heard, they were one noise, or none at all.
	//
	// The plain word remains for everything with no finer row, which is every
	// spell: a stilling is a stilling whatever is in your hands.
	FName Word = Verb;
	for (const TCHAR* Slot : { TEXT("weapon"), TEXT("offhand") })
	{
		const FName Held = Wearing(Who, Slot);
		if (Held.IsNone()) { continue; }
		const FName Fine(*(Verb.ToString() + TEXT(".") + Held.ToString()));
		if (Wardrobe->DeedSounds.Contains(Fine) || Wardrobe->Rites.Contains(Fine))
		{
			Word = Fine;
			break;
		}
	}
	// ---- WHAT IT LOOKS LIKE ----
	//
	// A ONE-SHOT, PLACED, NOT ATTACHED. The dust a citizen kicks up is
	// attached to them because it belongs to their walking; a cast is over
	// inside the interval and the caster may well have moved on by the time it
	// finishes, so this is left standing where the deed was done.
	//
	// It destroys itself. There is nothing to pool: a citizen casts a handful
	// of times in an evening, not once a stride.
	if (const FIntervalRite* Seen = Wardrobe->Rites.Find(Word))
	{
		if (Seen->System)
		{
			const FVector Where = At + FVector(0.f, 0.f, Seen->Rise);
			if (UNiagaraComponent* Shown = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
					GetWorld(), Seen->System, Where, FRotator::ZeroRotator,
					FVector(FMath::Max(0.05f, Seen->Scale)),
					/*bAutoDestroy*/ true, /*bAutoActivate*/ true))
			{
				Shown->SetCastShadow(false);
				// The colour is the whole of what tells two rites apart.
				Shown->SetVariableLinearColor(TEXT("Tint"), Seen->Tint);
			}
		}
	}

	const FIntervalFootfall* Noise = Wardrobe->DeedSounds.Find(Word);
	// Most deeds are silent on purpose. Banking makes no sound worth hearing.
	if (!Noise || Noise->Sounds.Num() == 0) { return; }
	Footfall(*Noise, At);
}

void AIntervalCitizens::Dye(USkeletalMeshComponent* Piece,
	UMaterialInterface* Fallback, float Shift)
{
	if (!Piece) { return; }

	// Sixteen shifts is as many as anybody can tell apart across a street, and
	// it turns "one instance per citizen per slot" -- which is hundreds --
	// into one per material per shift, which is dozens and is shared.
	const int32 Bucket = FMath::Clamp(FMath::FloorToInt(Shift * 16.f), 0, 15);
	const float Quantised = (static_cast<float>(Bucket) + 0.5f) / 16.f;

	const int32 Slots = Piece->GetNumMaterials();
	for (int32 Slot = 0; Slot < Slots; ++Slot)
	{
		UMaterialInterface* Source = Piece->GetMaterial(Slot);
		if (!Source) { Source = Fallback; }
		if (!Source) { continue; }
		// Already dyed -- this component was rebuilt, or the art shares a
		// material between parts, which it does constantly.
		if (Source->IsA<UMaterialInstanceDynamic>()) { continue; }

		const FString Id = FString::Printf(TEXT("%s|%d"), *Source->GetPathName(), Bucket);
		TObjectPtr<UMaterialInstanceDynamic>* Found = Dyed.Find(Id);
		if (!Found)
		{
			UMaterialInstanceDynamic* Made = UMaterialInstanceDynamic::Create(Source, this);
			if (!Made) { continue; }
			Made->SetScalarParameterValue(TEXT("Shift"), Quantised);
			Found = &Dyed.Add(Id, Made);
		}
		Piece->SetMaterial(Slot, Found->Get());
	}
}

UStaticMeshComponent* AIntervalCitizens::Hang(USkeletalMeshComponent* On,
	UStaticMeshComponent* Existing, const FIntervalPropPart& Piece,
	UMaterialInterface* Fallback) const
{
	if (!On || !Piece.Mesh)
	{
		if (Existing) { Existing->SetVisibility(false); }
		return Existing;
	}
	UStaticMeshComponent* Piecework = Existing;
	if (!Piecework)
	{
		Piecework = NewObject<UStaticMeshComponent>(const_cast<AIntervalCitizens*>(this));
		Piecework->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Piecework->RegisterComponent();
	}
	// ON THE BONE, so it moves with them. A hood parented to the actor rides
	// along at the right height and stares straight ahead while its owner
	// turns; parented to the head it is a hood.
	Piecework->AttachToComponent(On,
		FAttachmentTransformRules::SnapToTargetNotIncludingScale,
		Piece.Bone.IsNone() ? NAME_None : Piece.Bone);
	Piecework->SetStaticMesh(Piece.Mesh);
	// A garment with no material of its own takes the WEARER'S. The clothing
	// material bands by height in world space, so a skirt hung at the hips
	// comes out the colour of that citizen's tunic without anything having to
	// look up what colour their tunic is.
	if (UMaterialInterface* Cloth = Piece.Material ? Piece.Material.Get() : Fallback)
	{
		Piecework->SetMaterial(0, Cloth);
	}
	Piecework->SetRelativeTransform(FTransform(Piece.Rotation, Piece.Offset, Piece.Scale));
	Piecework->SetCastShadow(Piece.bCastShadow);
	Piecework->SetVisibility(true);
	return Piecework;
}

// Is this citizen carrying a consignment? The field is the world's own and
// arrives as raw JSON like every other; its mere presence is the answer, so
// nothing here parses it.
static bool bCarryingLoad(const FIntervalEntity& Who)
{
	const FString* Load = Who.Fields.Find(TEXT("consignment"));
	return Load && !Load->IsEmpty() && *Load != TEXT("null");
}

FName AIntervalCitizens::Wearing(const FIntervalEntity& Who, const TCHAR* Slot)
{
	// A SLOT HOLDS A STACK, NOT A NAME. The world sends
	// `equipment.weapon = {"item":"iron-hatchet","qty":1}`, the same shape an
	// inventory slot has, so the name is one level further in. Asking for the
	// slot itself returned the condensed JSON of the stack, which matches no
	// kit in the wardrobe -- so a wielded tool was simply never drawn, and
	// nothing anywhere said why. The bare-string form is still accepted in
	// case the world ever sends one.
	const FString Base = FString(TEXT("equipment.")) + Slot;
	for (const FString& Key : { Base + TEXT(".item"), Base })
	{
		if (const FString* Named = Who.Fields.Find(Key))
		{
			if (!Named->IsEmpty() && *Named != TEXT("null") && !Named->StartsWith(TEXT("{")))
			{
				return FName(**Named);
			}
		}
	}
	return NAME_None;
}

const FIntervalMotion* AIntervalCitizens::MotionFor(int32 Outfit, FName Verb) const
{
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe)
	{
		return nullptr;
	}
	// THE OUTFIT'S OWN TABLE FIRST. It exists only where an outfit is rigged
	// differently from the rest, and where it exists it is the only table whose
	// animations that skeleton will accept.
	if (Wardrobe->Outfits.IsValidIndex(Outfit))
	{
		if (const FIntervalMotion* Mine = Wardrobe->Outfits[Outfit].Motions.Find(Verb))
		{
			return Mine;
		}
	}
	return Wardrobe->Motions.Find(Verb);
}

bool AIntervalCitizens::HasMotion(int32 Outfit, FName Verb) const
{
	return MotionFor(Outfit, Verb) != nullptr;
}

void AIntervalCitizens::Dress(FIntervalCitizenView& View, const FIntervalEntity& Who, FName Verb) const
{
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe || !View.Mesh)
	{
		return;
	}

	// ---- WHAT IS IN THE HAND ----
	// A motion may bring its own tool: a swing is a swing, and what makes it
	// felling a tree rather than mining a seam is the hatchet. Otherwise it is
	// whatever the world says they have to hand.
	static const TCHAR* Slots[] = { TEXT("weapon"), TEXT("head"), TEXT("body"),
		TEXT("legs"), TEXT("offhand") };

	const FIntervalMotion* Motion = MotionFor(View.Outfit, Verb);
	const bool bTool = Motion && Motion->bHoldsTool && Motion->Held.Pieces.Num() > 0;

	// A SIGNATURE OF WHAT SHOULD BE SHOWING. Rebuilding a citizen's kit means
	// making components, so it is done when what they carry changes and not
	// sixty times a second; this is the cheapest honest way to know.
	FString Want = bTool ? Verb.ToString() : FString();
	for (const TCHAR* Slot : Slots)
	{
		Want += TEXT("|") + Wearing(Who, Slot).ToString();
	}
	if (Want == View.Carrying)
	{
		return;
	}
	// THE LOAD IS PART OF WHAT A CITIZEN IS WEARING, for the purpose of
	// knowing when to rebuild. Without it in the signature, taking up or
	// putting down a consignment changes nothing the kit notices and the
	// crate either never appears or never leaves.
	const bool bHauling = bCarryingLoad(Who);
	Want += bHauling ? TEXT("|haul") : TEXT("|");
	// §7d: AND THE FACE, which is not a kit and changes just as visibly.
	//
	// This signature exists so a citizen's body is rebuilt when what they are
	// carrying changes and not sixty times a second, and it listed only worn
	// things. So a citizen who stood at a looking-glass and chose a face kept
	// the old one until they happened to pick something up -- the deed landed,
	// the world held the new byte, and the window went on drawing yesterday.
	//
	// A face is a reason to rebuild for exactly the same reason a hat is.
	if (const FString* Chosen = Who.Fields.Find(TEXT("look")))
	{
		Want += TEXT("|") + *Chosen;
	}
	View.Carrying = Want;

	TArray<const FIntervalPropPart*> Pieces;
	if (bTool)
	{
		for (const FIntervalPropPart& Piece : Motion->Held.Pieces) { Pieces.Add(&Piece); }
	}
	for (const TCHAR* Slot : Slots)
	{
		// The motion's own tool is in that hand already; a sword does not get
		// carried through a tree.
		if (bTool && FCString::Strcmp(Slot, TEXT("weapon")) == 0)
		{
			continue;
		}
		const FName Item = Wearing(Who, Slot);
		if (Item.IsNone())
		{
			continue;
		}
		// ---- SOME NAMES ARE MINTED AND WILL NEVER BE IN A TABLE ----
		//
		// Almost every item in this world is a WORD -- `iron-hatchet`,
		// `steel-shield` -- and the wardrobe is keyed on those. Two are not.
		// A wayfarer's hood is `hood:<64 hex>:<tick>` and a fall stone is
		// `fallstone:<64 hex>:<tick>`: unique objects, minted for one citizen
		// at one moment, and the engine special-cases them in `isEquippable`
		// so they never appear in `EQUIPPABLE` at all.
		//
		// WHICH IS WHY NOTHING DREW THEM. `Worn.Find` on a key with a hash in
		// it finds nothing and the window drew an empty head -- and it drew it
		// for the one citizen in the world who had earned otherwise. The audit
		// that reports "every equippable word in the world has a mesh" was
		// telling the truth and still missing these, because they are not
		// words.
		//
		// The hood is worth more care than anything else a person can wear
		// here. It is granted for walking every trade, it survives the death
		// that annihilates everything else, it never expires, and it carries
		// the tick it was minted at -- the engine's own note calls it "the
		// only record in the world placed by history rather than by a
		// generator". A citizen wearing one and looking bare-headed is the
		// worst gap this window had.
		// The fold is `IntervalName::Row`, which is the same one the pack's
		// icons use. It was written out by hand here and nowhere else, which
		// is how the pack came to disagree with the wardrobe about the same
		// hood.
		const FName Row = IntervalName::Row(Item);
		if (const FIntervalKit* Kit = Wardrobe->Worn.Find(Row))
		{
			for (const FIntervalPropPart& Piece : Kit->Pieces) { Pieces.Add(&Piece); }
		}
	}

	// ---- AND WHAT THEY HAVE MASTERED, WHICH IS NOT WORN, IT IS TRUE ----
	//
	// Every loop above walks the EQUIPMENT: things a citizen picked up, can
	// put down, and can lose. This is the other kind. Mastery is a fact about
	// somebody, it cannot be traded or dropped, and the window said nothing
	// about it at all -- a citizen at a hundred in their own calling and one
	// who arrived this morning stood side by side and looked identical.
	//
	// THE FIELD IS DERIVED BY THE BRIDGE, like `calling` and `standing`
	// beside it: the engine owns the arithmetic and a window that worked out
	// a level from experience again would agree with it until one of the two
	// was edited. What arrives is the SKILL, or nothing, because the sash is
	// cut from what that trade handles and a boolean would leave this with
	// nothing to choose by.
	//
	// AND THERE IS ONLY EVER ONE. §5k of the engine: nothing unsworn passes
	// fifty and nothing outside your own trade passes seventy, so a citizen
	// masters their own calling or nothing. Nothing here accumulates.
	if (const FString* Mastered = Who.Fields.Find(TEXT("mastered")))
	{
		if (!Mastered->IsEmpty() && *Mastered != TEXT("null"))
		{
			const FName Sash(*(FString(TEXT("sworn.")) + *Mastered));
			if (const FIntervalKit* Kit = Wardrobe->Worn.Find(Sash))
			{
				for (const FIntervalPropPart& Piece : Kit->Pieces)
				{
					Pieces.Add(&Piece);
				}
			}
		}
	}

	// §11d: WHAT A RUNNER IS CARRYING, AND WHY IT MUST BE SEEN.
	//
	// Taking up a consignment empties the pack into a container the window
	// could not draw, so a hauler looked exactly like somebody carrying
	// nothing -- and this is the one state in the world that makes a citizen
	// lawfully strikeable by anybody. A window that hides it hides the risk,
	// and the risk is the whole reason the wage is worth taking.
	//
	// Drawn as an ordinary wardrobe entry keyed `haul`, so the art comes down
	// the same path as every worn thing and a founding that wants a different
	// bundle changes the table rather than this code.
	if (bHauling)
	{
		if (const FIntervalKit* Load = Wardrobe->Worn.Find(FName(TEXT("haul"))))
		{
			for (const FIntervalPropPart& Piece : Load->Pieces) { Pieces.Add(&Piece); }
		}
	}

	for (int32 i = 0; i < Pieces.Num(); ++i)
	{
		UStaticMeshComponent* Existing = View.Kit.IsValidIndex(i) ? View.Kit[i].Get() : nullptr;
		UStaticMeshComponent* Made = Hang(View.Mesh, Existing, *Pieces[i], View.Cloth);
		if (View.Kit.IsValidIndex(i)) { View.Kit[i] = Made; } else { View.Kit.Add(Made); }
	}
	for (int32 i = Pieces.Num(); i < View.Kit.Num(); ++i)
	{
		if (View.Kit[i]) { View.Kit[i]->SetVisibility(false); }
	}
}

uint32 AIntervalCitizens::KeyOfId(const FString& Id)
{
	// THE SAME NUMBER THE BROWSER WINDOW TAKES. It reads the first eight hex
	// digits of the citizen's id and derives their whole appearance from it --
	// tunic hue, skin, hair, eyes. Deriving a DIFFERENT number here would
	// dress the same person two ways in two windows, and "the woman in the
	// blue kirtle" would stop being a sentence anybody could act on.
	uint32 Key = 0;
	for (int32 i = 0; i < 8 && i < Id.Len(); ++i)
	{
		const TCHAR C = Id[i];
		uint32 Digit = 0;
		if (C >= '0' && C <= '9') { Digit = C - '0'; }
		else if (C >= 'a' && C <= 'f') { Digit = 10 + (C - 'a'); }
		else if (C >= 'A' && C <= 'F') { Digit = 10 + (C - 'A'); }
		else { break; }
		Key = Key * 16u + Digit;
	}
	return Key;
}

float AIntervalCitizens::UnitFromId(const FString& Id)
{
	// The world's id, hashed. Not the order they arrived in and not a random
	// number: those give a citizen different clothes in two windows, or new
	// ones tomorrow, and "the woman in the blue kirtle" is a sentence people
	// say to each other.
	uint32 H = 2166136261u;
	for (TCHAR C : Id)
	{
		H = (H ^ static_cast<uint32>(C)) * 16777619u;
	}
	H ^= H >> 13;
	return static_cast<float>(H & 0xffffu) / 65535.f;
}

FName AIntervalCitizens::VerbFor(const FIntervalEntity& Who, bool bMoving, int32 Outfit) const
{
	// THE WINDOW'S OWN FACT, FIRST. A citizen at nothing hit points is down
	// whatever else the world last said they were at; otherwise a corpse
	// stands there frozen mid-swing.
	if (const FString* Hp = Who.Fields.Find(TEXT("health")))
	{
		if (FCString::Atof(**Hp) <= 0.f)
		{
			return TEXT("felled");
		}
	}
	// ---- WHAT IS IN THE HANDS, WHICHEVER VERB IT IS ----
	//
	// `<verb>.<what is in the hand>` wins over `<verb>`, the weapon before the
	// off hand, and the plain word remains for everything the look asset has
	// no finer row for. It is the same rule `gather.<node>` has always used
	// and it is written once here because three copies of it drifted.
	//
	// THE WINDOW LEARNS NOTHING ABOUT THE WORLD FROM THIS. It reads two slots
	// and pastes two names together; which names are worth a row, and what
	// each one looks like, is entirely the look asset's business. A shield is
	// not special-cased here, and neither is a bow.
	auto InHand = [&](const FString& Base) -> FName
	{
		for (const TCHAR* Slot : { TEXT("weapon"), TEXT("offhand") })
		{
			const FName Held = Wearing(Who, Slot);
			if (Held.IsNone()) { continue; }
			const FName Fine(*(Base + TEXT(".") + Held.ToString()));
			if (HasMotion(Outfit, Fine)) { return Fine; }
		}
		return NAME_None;
	};

	// ---- WHAT THEY DID THIS INTERVAL ----
	//
	// `deed` is the world's own record of the verb a citizen performed on this
	// interval. The engine sets it in one place for every deed there is, and
	// drops it again at the start of the next interval, so it is present
	// exactly while it is true.
	//
	// IT WAS ALREADY ARRIVING AND NOTHING READ IT. The note further down said
	// "nothing arrives about anybody else's instant deeds, and a guess at one
	// would be this window inventing world state", and that was wrong: the
	// bridge forwards every field a citizen carries and this is one of them.
	// Believing otherwise is what kept sorcery invisible. All eleven spells
	// across both books are instant deeds, so not one of them ever sets an
	// `action`, so no citizen was ever seen to cast anything.
	//
	// ABOVE `action`, because an instant deed is what is happening NOW and an
	// action is what has been going on. A citizen who eats while felling a
	// tree is eating this second and felling the rest of the time.
	//
	// The look asset decides which deeds are worth a motion; one it has no row
	// for falls through to the action below, exactly as before.
	if (const FString* Did = Who.Fields.Find(TEXT("deed")))
	{
		if (!Did->IsEmpty() && *Did != TEXT("null"))
		{
			const FName Fine = InHand(*Did);
			if (!Fine.IsNone()) { return Fine; }
			const FName Plain(**Did);
			if (HasMotion(Outfit, Plain)) { return Plain; }
		}
	}

	// THE WORLD'S WORD, UNEXAMINED. `action` arrives as an object and the
	// frame parser flattens it a level, so the verb is already sitting here as
	// a string this file never has to have an opinion about.
	if (const FString* Act = Who.Fields.Find(TEXT("action.type")))
	{
		if (!Act->IsEmpty() && *Act != TEXT("null"))
		{
			// WHAT IS BEING GATHERED, if the world said. A swing is a swing;
			// felling a tree and cutting a seam differ in the tool and the
			// tempo, and the world already names the node being worked. The
			// more specific word wins where a level has one, exactly as it
			// does for `wall.roofed` over `wall`.
			// ---- AND WHAT IT IS BEING DONE WITH ----
			//
			// The same rule as the node below, on the other hand. Every
			// weapon in this world swung the same sword: a bow, a crossbow,
			// a handgonne, a staff, a chain and a spear all played
			// `Sword_Attack`, so an archer loosed an arrow by slashing the
			// air in front of them and a gunner did the same holding a gun.
			// It was reported as exactly that, and it is the one thing about
			// a fight that a viewer cannot fail to see.
			//
			// The world names what is in the hand and this window already
			// reads it to DRAW the thing, so keying on it costs nothing. The
			// finer word wins where the look asset has one and the plain
			// `attack` remains for everything it does not, which is most
			// blades: a sword swinging a sword needs no special row.
			{
				const FName Fine = InHand(*Act);
				if (!Fine.IsNone()) { return Fine; }
			}
			if (Bridge)
			{
				if (const FString* Node = Who.Fields.Find(TEXT("action.nodeId")))
				{
					if (const FIntervalEntity* At = Bridge->GetFrame().Nodes.Find(*Node))
					{
						// The node's TYPE, which is the word a level keys on --
						// `tree`, `iron-rock`, `fishing-spot`. Its sub-kind is
						// a finer thing than anybody needs to swing at.
						const FString Sub = At->Kind;
						if (!Sub.IsEmpty())
						{
							const FName Fine(*(*Act + TEXT(".") + Sub));
							if (HasMotion(Outfit, Fine)) { return Fine; }
						}
					}
				}
			}
			return FName(**Act);
		}
	}
	// ---- AND A DEED THE WORLD KEEPS NO RECORD OF ----
	//
	// Below the world's own word, deliberately: `gather`, `attack`, `attackp`,
	// `walk` and `raise` are ONGOING and the frame is the authority on them.
	// Everything else a citizen does is over by the time the frame is written,
	// so the frame says `null` and means it. See UIntervalBridgeSubsystem::Doing
	// for why the window is allowed to remember what the world does not.
	//
	// OURS ALONE, AND NOW ONLY A HEAD START. This was written when it looked
	// as though nothing arrived about anybody else's instant deeds. `deed`
	// does, and is read above. What this still buys is LATENCY: the world's
	// record arrives with the next frame, up to an interval later, and this
	// fires the moment the citizen presses the key, so their own hand moves at
	// once. Everybody else's arrives on the frame and is drawn from it.
	if (Bridge && !Bridge->Doing.IsNone()
		&& FPlatformTime::Seconds() < Bridge->DoingUntil
		&& !Who.Id.IsEmpty() && Who.Id == Bridge->GetFrame().Me.Id)
	{
		// THE SAME REFINEMENT AS THE BLOW ABOVE, and this one matters more.
		// `special` is the world's word for a weapon's OWN trick -- the
		// dagger's flurry, the mell's whole-body blow, the siphon's spout of
		// fire, the dragonbow's long shot -- four different things, and all
		// four were drawn as a magic missile because one row said so.
		const FName Fine = InHand(Bridge->Doing.ToString());
		if (!Fine.IsNone()) { return Fine; }
		if (HasMotion(Outfit, Bridge->Doing))
		{
			return Bridge->Doing;
		}
	}
	// ---- WALKING IS WHAT THE WORLD SAYS, NOT WHAT THE TILES SAY ----
	//
	// MEASURED: a citizen crosses exactly one tile per interval -- and only on
	// six intervals out of twenty-five. They step, stand for three, and step
	// again. Read off the tile difference alone, that is `walk`, `still`,
	// `walk`, `still` once a second, and the figure starts a stride, stops it,
	// and starts another without ever finishing one. It reads as somebody
	// marching in place, which is exactly what it was reported as.
	//
	// The world already says whether they are walking: `action` carries the
	// verb and how many steps are left in it. That is the authority, and the
	// tile difference is only the fallback for anybody the world says nothing
	// about -- a citizen halfway through a walk is walking on the ticks they
	// happen not to move on, and the animation should say so.
	// AND WHETHER THEIR HANDS ARE FULL. A consignment is carried for as long
	// as it takes to cross the island, which is most of what a hauler is ever
	// seen doing, and every one of them walked as though they were empty --
	// with a crate drawn riding on their shoulder, because the window has
	// always known. The refinement is the same one the blow and the node use.
	const bool bLoaded = bCarryingLoad(Who);
	auto Stride = [&](FName Plain) -> FName
	{
		// THE LOAD BEFORE THE HANDS, because a hauler's hands are ON the load:
		// somebody carrying a crate is not holding their shield up, whatever
		// the off-hand slot still says they own.
		if (bLoaded)
		{
			const FName Full(*(Plain.ToString() + TEXT(".hauling")));
			if (HasMotion(Outfit, Full)) { return Full; }
		}
		const FName Fine = InHand(Plain.ToString());
		return Fine.IsNone() ? Plain : Fine;
	};
	// ---- §7dn/§7dq: AND THE TWO TILES NOBODY WALKS ----
	//
	// The island has two thresholds: the squeeze into the Whitechalk barrow,
	// which takes nobody carrying more than three slots, and the Smother's
	// mouth, which takes nobody without a light. Both are a gap in rock, and
	// both were drawn as an ordinary stride, so a citizen entering the barrow
	// walked upright into a hillside.
	//
	// IT IS THE TILE, NOT THE PERMISSION. `bThresholdOpen` says whether the
	// citizen holding this window may pass; the motion is about anybody who IS
	// passing, which includes the stranger going in ahead of you. The frame
	// carries the tile only within two tiles of it, so the only crossings this
	// can draw are the ones somebody is close enough to watch, which is the
	// only time it matters.
	if (bMoving && ThresholdTileX >= 0)
	{
		const int32 TileX = FCString::Atoi(*Who.Fields.FindRef(TEXT("x")));
		const int32 TileY = FCString::Atoi(*Who.Fields.FindRef(TEXT("y")));
		if (TileX == ThresholdTileX && TileY == ThresholdTileY
			&& HasMotion(Outfit, TEXT("squeeze")))
		{
			// NOT through `Stride`. A squeeze is the one movement where what is
			// in your hands changes nothing about the shape of it: you go low
			// and you push, whether you are holding an axe or a crate, and a
			// hauler's crate is the reason you may not fit rather than a
			// variant of how you get through.
			return TEXT("squeeze");
		}
	}
	if (const FString* Doing = Who.Fields.Find(TEXT("action")))
	{
		if (Doing->Contains(TEXT("\"walk\"")))
		{
			return Stride(TEXT("walk"));
		}
	}
	return Stride(bMoving ? FName(TEXT("walk")) : FName(TEXT("still")));
}

namespace
{
	/**
	 * Centimetres a second, from the two tiles the world put a thing on.
	 *
	 * ONE INTERVAL IS THE WRONG WINDOW TO MEASURE IT OVER. A citizen walks in
	 * bursts -- one tile, then three intervals of nothing -- so the last pair
	 * of frames says either 200 cm/s or zero and never the truth, which is
	 * about fifty. The clip's rate then flips between its ceiling and its
	 * floor once a second. What is wanted is the pace, and a pace is an
	 * average; `Over` is how many intervals it is averaged across, and it is
	 * carried by the caller because only the caller knows who this is.
	 */
	float GroundSpeed(const FIntervalEntity& Now, const FIntervalEntity* Was, float Interval)
	{
		if (!Was || Interval <= KINDA_SMALL_NUMBER)
		{
			return 0.f;
		}
		// AND A JUMP HAS NO PACE. This drives the animation rate, so a ferry
		// crossing asked for a walk cycle at a hundred and fifty-eight tiles a
		// second and a beast respawning at its home asked for one across
		// however far it had wandered to die. Neither is locomotion: nothing in
		// this world travels more than a tile in an interval, so anything more
		// is the world putting a body somewhere, and a body being placed is not
		// moving at all.
		const int32 Leap = FMath::Max(FMath::Abs(Now.X - Was->X), FMath::Abs(Now.Y - Was->Y));
		if (Leap > 1)
		{
			return 0.f;
		}
		const float Tiles = FVector2D(static_cast<float>(Now.X - Was->X),
			static_cast<float>(Now.Y - Was->Y)).Size();
		return Tiles * UIntervalGeometry::GetTileSize() / Interval;
	}
}

void AIntervalCitizens::PlayBeast(USkeletalMeshComponent* InMesh,
	const FIntervalPropKind& Kind, FName Verb, const FString& Id, float Speed) const
{
	if (!InMesh)
	{
		return;
	}
	// A CREATURE WITH NO TABLE IS ON THE CITIZENS' SKELETON.
	//
	// The risen, the gibbet king and the five faces an incursion wears are
	// literally the citizens' own body, so the wardrobe's clips fit them and
	// are the right thing to play. Only the wild bestiary -- a wolf, a crab,
	// an ogre -- has a rig of its own, and only those carry a table. Falling
	// through to the wardrobe for the rest is not a fallback, it is the
	// correct answer for that half of the list.
	if (Kind.Motions.Num() == 0)
	{
		PlayVerb(InMesh, Verb, INDEX_NONE, 0.f);
		return;
	}
	const FIntervalBeastMotion* Motion = Kind.Motions.Find(Verb);
	if (!Motion)
	{
		// A word this creature has no clip for. Standing is the honest
		// fallback -- and if it has no standing either, whatever it is doing
		// now is better than a T pose.
		Motion = Kind.Motions.Find(TEXT("still"));
	}
	if (!Motion || !Motion->Anim)
	{
		return;
	}
	UIntervalAnimInstance* Inst = Cast<UIntervalAnimInstance>(InMesh->GetAnimInstance());
	if (!Inst)
	{
		return;
	}
	// OFF ITS OWN ID, so a pack of wolves is a pack and not one wolf drawn
	// four times breathing in unison. Only on the FIRST clip: starting every
	// later one at an offset would make a wolf begin its death a third of the
	// way through it.
	float StartAt = 0.f;
	if (!Inst->Arriving() && Motion->bLoop)
	{
		StartAt = (GetTypeHash(Id) % 997u) / 997.f * Motion->Anim->GetPlayLength();
	}
	// A quarter of a second. Long enough to see, short enough that a creature
	// reacting to something still looks like it reacted.
	// THE RATE FOLLOWS THE GROUND. See FIntervalBeastMotion::Pace.
	float Rate = Motion->Rate;
	if (Motion->Pace > 1.f)
	{
		Rate *= FMath::Clamp(Speed / Motion->Pace, 0.45f, 2.2f);
	}
	Inst->CrossFade(Motion->Anim, Rate, Motion->bLoop, 0.25f, StartAt);
}

void AIntervalCitizens::PlayVerb(USkeletalMeshComponent* InMesh, FName Verb, int32 Outfit,
	float Speed) const
{
	if (!InMesh)
	{
		return;
	}
	if (const FIntervalMotion* Motion = MotionFor(Outfit, Verb))
	{
		if (Motion->Anim)
		{
			if (UIntervalAnimInstance* Inst = Cast<UIntervalAnimInstance>(InMesh->GetAnimInstance()))
			{
				// See FIntervalMotion::Pace.
				float Rate = Motion->Rate;
				if (Motion->Pace > 1.f)
				{
					Rate *= FMath::Clamp(Speed / Motion->Pace, 0.45f, 2.2f);
				}
				Inst->CrossFade(Motion->Anim, Rate, Motion->bLoop, 0.25f);
			}
			return;
		}
	}
	// No row for that word. Fall back to walking or standing rather than to
	// nothing: a citizen doing something this build has never drawn should
	// still be a person standing there, not a mannequin in the T pose.
	if (UAnimSequence* Fallback = (Verb == TEXT("walk")) ? WalkAnimation.Get() : IdleAnimation.Get())
	{
		if (UIntervalAnimInstance* Inst = Cast<UIntervalAnimInstance>(InMesh->GetAnimInstance()))
		{
			Inst->CrossFade(Fallback, 1.f, true, 0.25f);
		}
	}
}

void AIntervalCitizens::UpdatePeople(float Alpha, const FVector& ViewLocation, bool bHaveView,
	float DeltaSeconds)
{
	const FIntervalFrame& Now = Bridge->GetFrame();
	const FIntervalFrame& Was = Bridge->GetPreviousFrame();
	if (!Ground)
	{
		TActorIterator<AIntervalGround> It(GetWorld());
		Ground = It ? *It : nullptr;
	}

	// IS THE TITLE CARD STILL UP? Asked once for everybody rather than once
	// per citizen: the answer is the same for all of them and the iterator is
	// not free. Nameplates stay down while it is, because a card is a composed
	// picture and half a dozen names drifting across the word INTERVAL reads
	// as clutter rather than as a world with people in it.
	bool bCardIsUp = false;
	{
		TActorIterator<AIntervalGate> Card(GetWorld());
		bCardIsUp = Card && Card->IsWaiting();
	}

	for (TPair<FString, FIntervalCitizenView>& Pair : Citizens)
	{
		Pair.Value.bSeenThisFrame = false;
	}

	// ---- THE WEATHER, ONCE, FOR EVERYBODY'S BOOTS ----
	//
	// Both of these are READ rather than reckoned. The hour worked out how wet
	// the ground is and how hard it is blowing from the world's own overcast
	// and rain, and wrote them on the collection every material reads; taking
	// them back off the same collection is the only arrangement in which the
	// dust, the smoke and the meadow are guaranteed to agree about the
	// weather. A second copy of the arithmetic here would agree until one of
	// them was edited.
	if (!Weathers)
	{
		Weathers = LoadObject<UMaterialParameterCollection>(
			nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky"));
	}
	float Dry = 1.f;
	FVector Gust = FVector::ZeroVector;
	if (Weathers)
	{
		// `Wet` and not `Rain`: dust stops when the ground is wet, and the
		// ground stays wet for a while after a shower stops. That lag is
		// exactly the behaviour wanted -- a road does not start smoking again
		// the moment the cloud passes.
		Dry = 1.f - FMath::Clamp(
			UKismetMaterialLibrary::GetScalarParameterValue(this, Weathers, TEXT("Wet")),
			0.f, 1.f);
		const float Blow = UKismetMaterialLibrary::GetScalarParameterValue(
			this, Weathers, TEXT("Gale"));
		// The prevailing direction, written down once in wind.hlsl: one island,
		// one wind. Dust is heavier than smoke and takes much less of it.
		Gust = FVector(0.82f, 0.57f, 0.f).GetSafeNormal()
			* (25.f + 120.f * FMath::Clamp(Blow, 0.f, 1.f));
	}


	for (const TPair<FString, FIntervalEntity>& Pair : Now.Players)
	{
		const FIntervalEntity& Who = Pair.Value;

		FIntervalCitizenView& View = Citizens.FindOrAdd(Pair.Key);
		if (!View.Mesh)
		{
			const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);

			// ---- A BODY IN PIECES ----
			// The figure is modular: a body, two arms, two legs, a head, all on
			// one skeleton. The FIRST part carries the animation and the rest
			// are told to follow its pose, which costs one evaluation for the
			// whole person however many parts they are made of.
			// ---- A CHOSEN FACE BEATS AN INHERITED ONE ----
			//
			// A citizen's appearance has always come from their key, which is
			// what makes "the woman in the blue kirtle" a sentence two people
			// can act on: nobody picked it, nobody can change it, and it is
			// the same in every window.
			//
			// But the world lets you choose. `set_look` writes a byte on the
			// citizen and the flat window has read it for as long as it has
			// existed -- `lookOf` takes `p.look` when it is there and falls
			// back to hashing the id when it is not. This window read only the
			// id, so a citizen who stood at a looking-glass and chose a face
			// kept the one they were born with here, and the two windows
			// disagreed about what somebody looks like.
			//
			// The world's answer wins where there is one. It is the same byte
			// on both sides, so the choice carries between windows exactly as
			// the inherited face already did.
			const FString* Chosen = Who.Fields.Find(TEXT("look"));
			const uint32 Key = (Chosen && !Chosen->IsEmpty())
				? static_cast<uint32>(FCString::Atoi(**Chosen) & 255)
				: KeyOfId(Pair.Key);

			// WHICH CLOTHES. The wardrobe holds several outfits and this
			// citizen's own key picks one, so the same person is dressed the
			// same in every window and the same tomorrow, and a crowd is a
			// crowd before a single colour has been changed.
			TArray<USkeletalMesh*> Parts;
			if (Wardrobe && Wardrobe->Outfits.Num() > 0)
			{
				View.Outfit = static_cast<int32>(Key % static_cast<uint32>(Wardrobe->Outfits.Num()));
				const FIntervalOutfit& Fit = Wardrobe->Outfits[View.Outfit];
				for (const TObjectPtr<USkeletalMesh>& Part : Fit.Parts)
				{
					if (Part) { Parts.Add(Part.Get()); }
				}
				// AND WHAT IS ON THEIR HEAD, off a different slice of the same
				// key -- so the man in the next field is not merely wearing the
				// same clothes as this one, he is the same man.
				if (Fit.Hair.Num() > 0)
				{
					const int32 Which =
						static_cast<int32>((Key >> 8) % static_cast<uint32>(Fit.Hair.Num()));
					if (Fit.Hair[Which]) { Parts.Add(Fit.Hair[Which].Get()); }
				}
			}
			if (Parts.Num() == 0 && Wardrobe)
			{
				for (const TObjectPtr<USkeletalMesh>& Part : Wardrobe->CitizenParts)
				{
					if (Part) { Parts.Add(Part.Get()); }
				}
			}
			if (Parts.Num() == 0 && CitizenMesh) { Parts.Add(CitizenMesh); }
			if (Parts.Num() == 0) { continue; }

			USkeletalMeshComponent* Mesh = nullptr;
			for (int32 i = 0; i < Parts.Num(); ++i)
			{
				USkeletalMeshComponent* Piece = NewObject<USkeletalMeshComponent>(this);
				Piece->SetupAttachment(RootComponent);
				Piece->SetMobility(EComponentMobility::Movable);
				Piece->SetSkeletalMesh(Parts[i]);
				Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Piece->RegisterComponent();
				if (i == 0)
				{
					// THE CROSS-FADING INSTANCE, not the single-node path. See
					// IntervalAnim.h: single node has no blend in it at all,
					// so every change of verb was a cut.
					Piece->SetAnimInstanceClass(UIntervalAnimInstance::StaticClass());
					Piece->SetAnimationMode(EAnimationMode::AnimationBlueprint);
					Mesh = Piece;
				}
				else
				{
					// Following a leader means never being animated at all:
					// the pose is copied, bone for bone, after the leader has
					// been evaluated once.
					//
					// ATTACHED TO THE LEADER, not to the actor. A follower takes
					// its bounds from whatever it hangs off, and parts hung off
					// the actor were culled the moment the camera could not see
					// the actor's origin -- which showed as a single floating
					// forearm with the rest of the person missing.
					Piece->AttachToComponent(Mesh,
						FAttachmentTransformRules::SnapToTargetIncludingScale);
					Piece->SetLeaderPoseComponent(Mesh);
					Piece->SetBoundsScale(2.f);
					View.Limbs.Add(Piece);
				}
			}

			// THEIR OWN CLOTHES. One material instance per citizen, holding
			// one number: which of them this is. Everything the material does
			// with it -- the colour of the tunic, of the hose, of their skin --
			// is drawn from that, so a street is a street and not a rack of
			// the same figure. The number is a hash of the world's OWN id for
			// them, so they are dressed the same in every window and the same
			// tomorrow, and nothing had to be told to anybody.
			// THEIR OWN COLOURS, not their own material.
			//
			// This used to paint one material over every slot of the figure,
			// which was right when the figure was the engine's grey mannequin
			// and had nothing to lose. It is wrong now: the art arrives with a
			// material per region, each named for what it is and carrying the
			// colour the artist chose, and flattening that to one material
			// throws away the only thing that makes a farmer look like a
			// farmer. So every slot keeps ITS OWN material and is simply told
			// which citizen is wearing it.
			//
			// `Hue` is still the browser window's arithmetic on the same key,
			// so a person is recognisably themselves in either window.
			UMaterialInterface* Skin = Wardrobe ? Wardrobe->PersonMaterial.Get() : nullptr;
			const float Shift = static_cast<float>(Key % 360u) / 360.f;
			Dye(Mesh, Skin, Shift);
			for (const TObjectPtr<USkeletalMeshComponent>& Limb : View.Limbs)
			{
				Dye(Limb.Get(), Skin, Shift);
			}
			if (Skin)
			{
				// The old procedural material, if a level still names one:
				// it wants the whole set of numbers, not just the shift.
				View.Cloth = UMaterialInstanceDynamic::Create(Skin, this);
				View.Cloth->SetScalarParameterValue(TEXT("Who"), UnitFromId(Pair.Key));
				View.Cloth->SetScalarParameterValue(TEXT("Hue"), Shift);
				View.Cloth->SetScalarParameterValue(TEXT("Skin"),
					static_cast<float>(Key % 6u));
				View.Cloth->SetScalarParameterValue(TEXT("Hair"),
					static_cast<float>((Key >> 4) % 7u));
			}
			if (Wardrobe)
			{
				for (const FIntervalPropPart& Piece : Wardrobe->Clothing)
				{
					View.Wearing.Add(Hang(Mesh, nullptr, Piece, View.Cloth));
				}
			}
			View.Mesh = Mesh;

			UWidgetComponent* Plate = NewObject<UWidgetComponent>(this);
			Plate->SetupAttachment(RootComponent);
			Plate->SetMobility(EComponentMobility::Movable);
			// Screen space: always facing, always legible, no facing to get
			// backwards. See the note on UIntervalPlateWidget.
			Plate->SetWidgetSpace(EWidgetSpace::Screen);
			Plate->SetWidgetClass(UIntervalPlateWidget::StaticClass());
			Plate->SetDrawSize(FVector2D(320.f, 44.f));
			Plate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Plate->RegisterComponent();
			View.Plate = Plate;
		}
		View.bSeenThisFrame = true;

		FVector Location;
		bool bMoving = false;
		DrawnPosition(Pair.Key, Who, Was.Players, Alpha, Now.Tick, Location, bMoving);

		if (bMoving)
		{
			const FIntervalEntity* From = Was.Players.Find(Pair.Key);
			View.Yaw = FMath::RadiansToDegrees(FMath::Atan2(
				static_cast<float>(Who.Y - From->Y), static_cast<float>(Who.X - From->X)));
		}
		// FACING WHAT THEY ARE WORKING ON. A citizen swinging a hatchet at a
		// tree behind them is the sort of thing that is invisible until it is
		// pointed out and then impossible to stop seeing. The world says which
		// node they are at; where that node is, is told.
		else if (Bridge)
		{
			if (const FString* Node = Who.Fields.Find(TEXT("action.nodeId")))
			{
				if (const FIntervalEntity* At = Bridge->GetFrame().Nodes.Find(*Node))
				{
					if (At->X != Who.X || At->Y != Who.Y)
					{
						View.Yaw = FMath::RadiansToDegrees(FMath::Atan2(
							static_cast<float>(At->Y - Who.Y),
							static_cast<float>(At->X - Who.X)));
					}
				}
			}
		}

		// AND THEY TURN TO IT. The heading is read off the tile they came
		// from, so it moves in eighth turns; applied straight, somebody
		// rounding a corner is facing east and then, on one frame, north.
		// A person turns faster than an animal does.
		View.YawShown = View.bYawKnown
			? FMath::FixedTurn(View.YawShown, View.Yaw, 520.f * DeltaSeconds)
			: View.Yaw;
		View.bYawKnown = true;

		// The mannequin's feet are at its origin, so no lift is needed.
		// ...plus however the art is mounted. See IntervalLook::CitizenFacingYaw:
		// these figures front along Y, not the +X Unreal assumes.
		const UIntervalLook* Mounted = UIntervalLook::Resolve(Look);
		const FRotator Facing(0.f,
			View.YawShown + (Mounted ? Mounted->CitizenFacingYaw : 0.f), 0.f);
		// HOW FAR THEY HAVE COME SINCE LAST FRAME, taken before the mesh is
		// moved, because afterwards there is nothing left to compare against.
		const float Stepped = View.bYawKnown
			? static_cast<float>(FVector::Dist2D(View.Mesh->GetComponentLocation(), Location))
			: 0.f;
		View.Mesh->SetWorldLocationAndRotation(Location, Facing);

		// ---- AND THE CAMERA ORBITS THE BODY, NOT THE TEMPLATE'S PAWN ----
		//
		// The view is the third-person template's pawn on a spring arm, and
		// the citizen a player is looking at is drawn HERE, as a mesh on this
		// actor, at an interpolated position. Nothing kept the two together.
		// So turning the camera swung it round wherever the pawn happened to
		// be standing, which is near the citizen and never exactly on them:
		// "the camera rotation is a little weird, the character should be in
		// center, so the camera should rotate around the character. Now idk
		// what it centers but it feels weird."
		//
		// The pawn is moved to the drawn body every frame, which makes the
		// arm's pivot the body by construction rather than by coincidence.
		// It is COSMETIC, like every other interpolation in this file: the
		// pawn is a camera mount and no deed has ever been derived from where
		// it stands.
		if (Bridge && !Who.Id.IsEmpty() && Who.Id == Bridge->GetFrame().Me.Id)
		{
			if (const APlayerController* PC = GetWorld()
				? GetWorld()->GetFirstPlayerController() : nullptr)
			{
				if (APawn* Seat = PC->GetPawn())
				{
					// TELEPORTED, not swept. A swept move is a move that can
					// be BLOCKED, and a camera mount that catches on a fence
					// is the fault this is fixing wearing a different hat.
					Seat->SetActorLocation(Location, false, nullptr,
						ETeleportType::TeleportPhysics);
				}
			}
		}

		// THEIR OWN BUILD. One mesh is all there is, so the difference between
		// two people has to come out of what can be done to it: a hand's
		// breadth of height, and a little more or less across the shoulders.
		// Both from their own number, so they are the same person tomorrow.
		const UIntervalLook* Sizes = UIntervalLook::Resolve(Look);
		const float Stature = (Sizes && Sizes->CitizenScale > 0.f)
			? Sizes->CitizenScale : CitizenScale;
		const float Unit = UnitFromId(Pair.Key);
		const float Tall = 0.93f + 0.13f * Unit;
		const float Broad = 0.94f + 0.12f * FMath::Frac(Unit * 7.3f);
		View.Mesh->SetWorldScale3D(FVector(Stature * Broad, Stature * Broad,
			Stature * Tall));

		// ---- AND A LAMP, WHERE THERE IS A ROOF ----
		//
		// Only for the citizen whose window this is, and only while they are
		// under one. `RoofTopAtTile` is the ground's own answer, which is the
		// same test the roof uses to decide it is a roof at all.
		if (Bridge && Who.Id == Bridge->GetFrame().Me.Id)
		{
			const AIntervalGround* Land = Ground.Get();
			// ---- §7dq: AND IN A CAVE IT IS THE ONLY LIGHT THERE IS ----
			//
			// The lamp was written as a ROOM's light: a hearth, so an interior
			// is not black, for the citizen whose window this is and only while
			// they stand under a roof. The Smother is not a room. There is rock
			// over it, nothing coming in at any window, and the mouth refuses
			// anybody who is not carrying something burning -- so in there the
			// thing a citizen holds is the whole of what they can see by.
			//
			// Same component, because a second point light attached to the same
			// mesh for the same purpose is two things to keep in step. What
			// differs is the CHARACTER: a hearth fills a room and a torch makes
			// a circle you walk inside, so underground it is brighter and
			// reaches less far.
			//
			// AND IT GOES OUT. `bLit` is the engine's answer and a torch burns
			// down (§7dq-iii), so this can fall to false under a citizen who is
			// already in the dark, which is exactly what the item is for.
			const bool bInCave = Bridge->GetFrame().Surface
				.Equals(TEXT("cave"), ESearchCase::IgnoreCase);
			const bool bCarried = bInCave && Bridge->GetFrame().bLit;
			const bool bUnderRoof = (Land && Land->IsRoofedAtTile(Who.X, Who.Y))
				|| bCarried;
			if (bUnderRoof && !View.Lamp)
			{
				View.Lamp = NewObject<UPointLightComponent>(this);
				View.Lamp->SetupAttachment(View.Mesh);
				View.Lamp->SetMobility(EComponentMobility::Movable);
				View.Lamp->SetCastShadows(false);
				View.Lamp->RegisterComponent();
				View.Lamp->AttachToComponent(View.Mesh,
					FAttachmentTransformRules::KeepRelativeTransform);
				// Above head height, so it lights the floor and the near
				// walls rather than the top of a skull.
				View.Lamp->SetRelativeLocation(FVector(0.f, 0.f, 320.f));
				// WARM AND SHORT. A room is lit by a hearth and a doorway, so
				// the colour is the hearth's; the radius stops at the walls
				// this room has, which is what keeps it from glowing through
				// them into the street.
				View.Lamp->SetLightColor(FLinearColor(1.f, 0.82f, 0.58f));
				// WIDE AND SOFT, NOT BRIGHT AND CLOSE. The first cut was nine
				// thousand over nine metres, which lit the room and blew the
				// citizen standing under it into a white blob -- the one thing
				// in the room a player is actually looking at. Spread over a
				// larger radius at a third of the strength, the floor and the
				// near walls come up and the figure keeps its shape.
				//
				// AND THEN A THIRD OF THAT AGAIN. Three thousand two hundred
				// still blew out, and the reason is not the lamp on its own:
				// a room's floor here is flagstone at 0.27 albedo, the auto
				// exposure is set by a frame that is mostly sunlit street, and
				// a light bright enough to be read against that exposure is
				// far brighter than the floor can take. Photographed indoors
				// at night it was a white disc with the citizen invisible in
				// the middle of it, which is the complaint this lamp exists to
				// answer, arrived at from the other direction.
				//
				// Nine hundred lights the room and leaves the flagstones as
				// stone. What makes the figure legible is the WALL CUT, not
				// the lamp; the lamp only has to stop the room being black.
				//
				// AND NINE HUNDRED WAS STILL BLINDING, for a reason that has
				// nothing to do with the lamp: the exposure. At night the eye
				// opens right up, so the number that reads as a hearth at noon
				// reads as a magnesium flare at midnight, and the citizen --
				// standing directly under it -- is the first thing to go. The
				// photograph that settled it has a nameplate floating over a
				// white hole with no figure in it.
				//
				// So the lamp is set from the HOUR. `Night` is the one number
				// the whole window already agrees on, and a hearth is a hearth
				// against a dark room, not against a dark room seen through a
				// wide-open iris. By day it is nearly nothing, which is right:
				// by day the roof has dissolved and the sky is doing the work.
				// FALLING OFF LIKE A ROOM, not like a bulb. Inverse square
				// puts everything in the first metre and nothing at the wall.
				View.Lamp->SetUseInverseSquaredFalloff(false);
				View.Lamp->SetLightFalloffExponent(2.f);
			}
			if (View.Lamp)
			{
				View.Lamp->SetVisibility(bUnderRoof);
				// HOW DARK IT IS OUTSIDE, off the collection the hour writes
				// to, so this needs no second opinion about the time of day
				// and cannot disagree with the sky.
				//
				// The collection this actor already holds, not a fresh
				// LoadObject: this runs once per drawn citizen per frame, and
				// loading an asset by path in that loop is exactly the kind of
				// instrumentation that quietly costs the game thread its frame.
				if (!Weathers)
				{
					Weathers = LoadObject<UMaterialParameterCollection>(
						nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky"));
				}
				const float Dark = Weathers
					? UKismetMaterialLibrary::GetScalarParameterValue(this, Weathers, TEXT("Night"))
					: 0.f;
				// The two numbers live in the look asset so they can be tuned
				// between two photographs instead of between two builds. See
				// IntervalLook.h for the four rounds of this that preceded it.
				float ByDay = 60.f, ByNight = 160.f, Reach = 1050.f;
				if (const UIntervalLook* Tuned = UIntervalLook::Resolve(nullptr))
				{
					ByDay = Tuned->LampByDay;
					ByNight = Tuned->LampByNight;
					Reach = Tuned->LampReach;
				}
				// §7dq: a torch is not a hearth. Underground the sun is down to
				// a sixth of nothing, so the carried light has to be the light
				// in the shot rather than a lift on top of one, and it has to
				// fall off inside a few tiles or the cave reads as a lit room
				// with a dark edge.
				if (bCarried)
				{
					View.Lamp->SetAttenuationRadius(Reach * 0.55f);
					View.Lamp->SetIntensity(ByNight * 1.35f);
					View.Lamp->SetLightColor(FLinearColor(1.f, 0.74f, 0.42f));
				}
				else
				{
					View.Lamp->SetAttenuationRadius(Reach);
					View.Lamp->SetIntensity(FMath::Lerp(ByDay, ByNight,
						FMath::Clamp(Dark, 0.f, 1.f)));
					View.Lamp->SetLightColor(FLinearColor(1.f, 0.82f, 0.58f));
				}
			}
		}

		// ---- AND THE DUST THEY LIFT ----
		//
		// ATTACHED TO THE FIGURE, not placed at it. That is not tidiness: the
		// emitter spawns per unit of the component's OWN travel, so attaching
		// it is what tells it somebody is walking. Nothing here asks whether
		// they are, nothing turns it on and off, and a citizen who stops
		// raising dust has stopped because they stopped moving.
		if (Sizes && Sizes->StepDust)
		{
			if (!View.Dust)
			{
				View.Dust = NewObject<UNiagaraComponent>(this);
				View.Dust->SetupAttachment(View.Mesh);
				View.Dust->SetMobility(EComponentMobility::Movable);
				View.Dust->SetAutoActivate(false);
				View.Dust->SetAutoDestroy(false);
				View.Dust->SetCastShadow(false);
				View.Dust->RegisterComponent();
				View.Dust->AttachToComponent(View.Mesh,
					FAttachmentTransformRules::KeepRelativeTransform);
				View.Dust->SetAsset(Sizes->StepDust);
				// AN ABSOLUTE SCALE. The figure above is scaled by this
				// citizen's own build, and a tall citizen does not kick up a
				// taller puff -- dust is a property of the ground, not of who
				// is standing on it.
				View.Dust->SetAbsolute(false, false, true);
				View.Dust->SetRelativeLocation(FVector(0.f, 0.f, Sizes->StepDustRise));
				View.Dust->SetWorldScale3D(
					FVector(FMath::Max(0.01f, Sizes->StepDustScale)));
			}
			View.Dust->SetVariableFloat(TEXT("Dry"), Dry);
			View.Dust->SetVariableVec3(TEXT("Wind"), Gust);
			// ACTIVATED EVERY FRAME UNTIL IT TAKES, not once when it is made.
			//
			// Niagara refuses to activate a system that is not ready to run --
			// still compiling, most often, which is exactly the state
			// everything is in the moment a world starts. It says nothing; the
			// component simply stays inactive. Activating once at creation
			// therefore works or does not work depending on how busy the
			// editor was that second, which is the worst kind of bug to have.
			if (!View.Dust->IsActive())
			{
				View.Dust->Activate();
			}
		}

		// ---- AND WHAT A SPELL LEFT ON THEM ----
		//
		// THE OTHER HALF OF SORCERY. A rite is the casting and it is over
		// inside the interval; these are the conditions it leaves behind, and
		// they are the half that matters to the person it landed on. The
		// bridge forwards them as `marks.<word>` holding the intervals
		// REMAINING, so nothing here does arithmetic with the world's clock:
		// a count above nothing means it is still on them.
		//
		// ONE COMPONENT, NOT SIX. A citizen can carry several at once and
		// drawing all of them would be a bonfire around somebody who is still
		// only standing there. The list below is walked in order and the FIRST
		// match wins, so the order IS the priority: burning before rotting
		// before withered, because a citizen who is on fire is on fire
		// whatever else is also true of them. `rooted` and `stilled` come last
		// because they are the two that are already legible -- somebody held
		// in place is visibly not moving.
		if (Sizes && Sizes->Marks.Num() > 0)
		{
			static const TCHAR* const Worst[] = {
				TEXT("burning"), TEXT("rotting"), TEXT("withered"),
				TEXT("branded"), TEXT("rooted"), TEXT("stilled") };
			FName Worn;
			for (const TCHAR* Word : Worst)
			{
				const FString* Left = Who.Fields.Find(
					FString(TEXT("marks.")) + Word);
				if (Left && FCString::Atof(**Left) > 0.f)
				{
					Worn = FName(Word);
					break;
				}
			}
			const FIntervalRite* Mark = Worn.IsNone()
				? nullptr : Sizes->Marks.Find(Worn);
			if (Mark && Mark->System)
			{
				if (!View.Mark)
				{
					View.Mark = NewObject<UNiagaraComponent>(this);
					View.Mark->SetupAttachment(View.Mesh);
					View.Mark->SetMobility(EComponentMobility::Movable);
					View.Mark->SetAutoActivate(false);
					View.Mark->SetAutoDestroy(false);
					View.Mark->SetCastShadow(false);
					View.Mark->RegisterComponent();
					View.Mark->AttachToComponent(View.Mesh,
						FAttachmentTransformRules::KeepRelativeTransform);
					// ABSOLUTE SCALE, like the dust: a tall citizen does not
					// burn bigger.
					View.Mark->SetAbsolute(false, false, true);
				}
				// SWAPPED ONLY WHEN THE WORD CHANGES. Setting the asset every
				// frame restarts the system every frame, which is a mark that
				// never gets past its first few particles.
				if (View.MarkWord != Worn)
				{
					View.MarkWord = Worn;
					View.Mark->Deactivate();
					View.Mark->SetAsset(Mark->System);
					View.Mark->SetRelativeLocation(
						FVector(0.f, 0.f, Mark->Rise));
					View.Mark->SetWorldScale3D(
						FVector(FMath::Max(0.05f, Mark->Scale)));
					View.Mark->SetVariableLinearColor(TEXT("Tint"), Mark->Tint);
				}
				// Activated until it takes, for the same reason the dust is:
				// a system that is still compiling refuses silently.
				if (!View.Mark->IsActive())
				{
					View.Mark->Activate();
				}
			}
			else if (View.Mark && !View.MarkWord.IsNone())
			{
				// IT IS OVER. Deactivated rather than destroyed, because the
				// same citizen is likely to be marked again and a component
				// per casting is a component per casting for ever.
				View.MarkWord = FName();
				View.Mark->Deactivate();
			}
		}
		// ---- AND THE SOUND OF IT ----
		//
		// COUNTED IN CENTIMETRES WALKED, not in seconds. Exactly the same
		// trick as the dust, and for the same reason: a footfall timed off a
		// clock has to be started and stopped by somebody who knows whether
		// this citizen is walking, and a footfall spaced along the ground
		// simply happens when they cross the ground and not otherwise. It also
		// keeps up by itself when somebody is moving faster than the walk was
		// cut for.
		if (Sizes && bMoving && Stepped > 0.f)
		{
			View.Walked += Stepped;
			const float Every = FMath::Max(10.f, Sizes->StepEvery);
			if (View.Walked >= Every)
			{
				View.Walked = FMath::Fmod(View.Walked, Every);
				const bool bNear = !bHaveView
					|| FVector::DistSquared(ViewLocation, Location)
					   < FMath::Square(FMath::Max(1.f, Sizes->StepHeard));
				const FName Word = Ground
					? Ground->GroundWordAtTile(Who.X, Who.Y) : FName();
				const FIntervalFootfall* Fall = bNear && !Word.IsNone()
					? Sizes->Footfalls.Find(Word) : nullptr;
				if (Fall && Fall->Sounds.Num() > 0)
				{
					Footfall(*Fall, Location);
				}
			}
		}
		else
		{
			View.Walked = 0.f;
		}

		// WHERE THEY ARE STANDING AND WHICH WAY THEY FACE, handed to the
		// clothing material. It bands the clothes by height up the body and
		// needs a floor to measure from; the obvious world-to-local transform
		// in the graph comes back constant on a skinned mesh and paints the
		// whole figure one colour. This is known exactly right here, having
		// just been used to place them.
		if (View.Cloth)
		{
			// The material bands the body in centimetres from the feet, so a
			// figure scaled to nine tenths needs its bands scaled with it or
			// a short citizen wears their belt round their chest.
			View.Cloth->SetScalarParameterValue(TEXT("Tall"), Tall);
			View.Cloth->SetVectorParameterValue(TEXT("Foot"), FLinearColor(Location));
			const FVector Fwd = Facing.Vector();
			View.Cloth->SetVectorParameterValue(TEXT("Fore"), FLinearColor(Fwd));
		}

		// ---- WHAT THEY ARE DOING ----
		// The world says so, in its own word, and the level says what that word
		// looks like. Two of these the world does not say and the window works
		// out: `still`, for a citizen with nothing being said about them, and
		// `felled`, from hit points -- both the window's own, the way `roofed`
		// is, and both marked as such where they are decided.
		// EVERY FRAME, for the same reason the beasts are: asking for the clip
		// that is already arriving does nothing except update its rate, and
		// that is what stops the feet sliding when somebody is crossing the
		// ground slower than the walk was cut for.
		const FName Verb = VerbFor(Who, bMoving, View.Outfit);
		View.Verb = Verb;
		View.bWalking = bMoving;

		// AND WHAT IT SOUNDS LIKE. Read from the world's own `deed` rather
		// than from the verb settled above, because that verb may have come
		// from an ongoing action or from this window's own head start on the
		// local citizen, and a sound should follow the world. A deed with no
		// row in the look is silent.
		//
		// AND AN ACTION IS A SOUND TOO, which it was not. Everything here read
		// `deed` alone, and `gather`, `attack` and `attackp` are not deeds:
		// they set an `action` and run on by themselves. So the largest noise
		// in the world -- an axe in a tree, a pick in a rock, a blade landing
		// -- had a row in the look, a wav on disk, and no path to either. The
		// deed still wins where both are present, because a citizen eating
		// mid-fight is eating this second and fighting the rest of the time.
		{
			const FString* Did = Who.Fields.Find(TEXT("deed"));
			const bool bReal = Did && !Did->IsEmpty() && *Did != TEXT("null");
			const FString* Act = Who.Fields.Find(TEXT("action.type"));
			const bool bAct = !bReal && Act && !Act->IsEmpty() && *Act != TEXT("null");
			// §6c: AND GOING DOWN IS NOT A DEED, so nothing in `deed` or
			// `action` will ever carry it. The world reports hit points and
			// never announces a death -- the same reason `felled` is this
			// window's own word for the MOTION a few lines above -- so the
			// window has to notice it here or a citizen dies in silence.
			//
			// It takes priority over whatever they were doing, because being
			// struck down mid-swing is the thing that just happened, and it
			// speaks once: `DeedHeard` only speaks when the word CHANGES, so
			// there is one noise at the moment of death and nothing for the
			// five intervals the body lies there.
			int32 Hp = 0;
			if (const FString* Told = Who.Fields.Find(TEXT("health")))
			{
				Hp = FCString::Atoi(**Told);
			}
			const FName Word = Hp <= 0
				? FName(TEXT("felled"))
				: (bReal ? FName(**Did) : (bAct ? FName(**Act) : NAME_None));
			DeedHeard(Pair.Key, Who, Word, Location, bAct, Now.Tick);
		}
		if (View.PacedAt != Now.Tick)
		{
			View.PacedAt = Now.Tick;
			const float Raw = GroundSpeed(Who, Was.Players.Find(Pair.Key),
				Bridge ? Bridge->GetTickSeconds() : 1.f);
			View.Pace = (View.Pace <= 0.f) ? Raw : FMath::Lerp(View.Pace, Raw, 0.34f);
		}
		PlayVerb(View.Mesh, Verb, View.Outfit, View.Pace);
		Dress(View, Who, Verb);

		if (View.Bubble)
		{
			// IT FOLLOWS THE DRAWN FIGURE, not the tile, or somebody speaking
			// while they walk leaves their words behind on the pavement.
			if (FPlatformTime::Seconds() > View.BubbleUntil)
			{
				View.Bubble->SetVisibility(false);
			}
			else
			{
				View.Bubble->SetVisibility(true);
				View.Bubble->SetWorldLocation(Location + FVector(0.f, 0.f, BubbleHeight));
				if (!View.bSpokenShown)
				{
					if (UIntervalBubbleWidget* W = Cast<UIntervalBubbleWidget>(
						View.Bubble->GetUserWidgetObject()))
					{
						W->Set(View.Spoken, View.bSpokenFar);
						View.bSpokenShown = true;
					}
				}
			}
		}

		// §7ca: WHAT THEY JUST TOOK, before anything about plates.
		//
		// Deliberately outside the block below. The health bar lives on the
		// nameplate and so is subject to `bShowNamePlates`, the title card and
		// the plate distance; a blow landing is not a label and must not
		// disappear because somebody turned names off to take a photograph.
		SplatsFor(View, Who, Location,
			Bridge && Pair.Key == Bridge->GetPlayerId());

		if (View.Plate)
		{
			const bool bNear = !bHaveView
				|| FVector::DistSquared(Location, ViewLocation) < PlateMaxDistance * PlateMaxDistance;
			// NOT WHILE THE TITLE CARD IS UP. The card is a composed picture
			// over the country and other citizens' names floated across it,
			// which reads as clutter rather than as life: half a dozen labels
			// drifting over the word INTERVAL. They come back the moment the
			// gate opens, which is when they start being worth reading.
			View.Plate->SetVisibility(bShowNamePlates && bNear && !bCardIsUp);
			if (bShowNamePlates && bNear && !bCardIsUp)
			{
				// Whatever the world called them, and whatever it says they
				// are doing. `action.type` when the world gave the action a
				// shape, the whole of it when it did not. Both are strings
				// from a frame, shown as they arrived.
				const FString* Name = Who.Fields.Find(TEXT("name"));
				const FString* Doing = Who.Fields.Find(TEXT("action.type"));
				if (!Doing) { Doing = Who.Fields.Find(TEXT("action")); }
				FString LabelText = (Name && !Name->IsEmpty()) ? *Name : Pair.Key.Left(8);

				// WHO THEY ARE, NOT ONLY WHAT THEY ARE CALLED.
				//
				// A name over a head is the least interesting thing about a
				// citizen in a world with callings in it: what a stranger
				// wants to know before they speak is whether this is a smith
				// or a mourner or an archer, and how far they have come. Both
				// are derived by the engine and sent by the bridge -- see
				// `players` there -- so this window only has to read them.
				const FString* Calling = Who.Fields.Find(TEXT("calling"));
				const FString* Standing = Who.Fields.Find(TEXT("standing"));
				if (Calling && !Calling->IsEmpty())
				{
					LabelText += TEXT(", ") + *Calling;
				}
				if (Standing && !Standing->IsEmpty())
				{
					// The world sends a number; it arrives as text the way a
					// double prints, so it is made whole again here.
					LabelText += FString::Printf(TEXT(" (%d)"),
						FMath::RoundToInt(FCString::Atof(**Standing)));
				}
				// The deed goes on its own line below, in its own hand. See
				// UIntervalPlateWidget::Doing.
				FString Deed_ = (Doing && !Doing->IsEmpty()
					&& *Doing != TEXT("idle")) ? *Doing : FString();

				// ---- AND A RUNG SOMEBODY ELSE CLIMBED ----
				//
				// Standing is the engine's own sum of this citizen's skill
				// levels, and it is already on the plate, so a rise of one is
				// a level gained and nothing new has to cross the wire.
				//
				// It cannot say WHICH craft. Standing is a total, and the only
				// other way to know would be to carry everybody's experience
				// and work the ladder out again in this window, which is the
				// engine's arithmetic and not ours to copy. "levelled up" is
				// what a neighbour would see anyway, and it is enough to
				// congratulate somebody for.
				//
				// See FIntervalCitizenView::StandingWas for why this is said
				// over their head rather than in the chat.
				bool bCrowed = false;
				if (Standing && !Standing->IsEmpty())
				{
					const int32 StandsAt = FMath::RoundToInt(FCString::Atof(**Standing));
					if (View.StandingWas >= 0 && StandsAt > View.StandingWas)
					{
						View.RoseAt = FPlatformTime::Seconds();
					}
					View.StandingWas = StandsAt;
				}
				// FIVE SECONDS, and it takes the deed line for that long. A
				// citizen is gathering for hours and climbs a rung for a
				// moment, so the moment is the thing worth the line.
				if (FPlatformTime::Seconds() - View.RoseAt < 5.0)
				{
					Deed_ = TEXT("levelled up");
					bCrowed = true;
				}
				// AND A WOUND, WHICH A BEAST HAS AND A PERSON DID NOT.
				//
				// The ten-notch bar was given to beasts and never to citizens,
				// so a fight between people showed nothing at all -- and §11d
				// makes exactly that fight a thing the world expects to
				// happen, since a hauler carrying a consignment is the one
				// citizen anybody may lawfully strike. Found by killing
				// goblins at the pound: the citizen stood at 58 of 64 with
				// nothing over their head, while the goblin they were fighting
				// carried a bar.
				//
				// It rides on the name plate rather than in a second widget,
				// because a person already HAS a plate and two of them over
				// one head is a HUD. Shown only when hurt, like the beast's.
				// `TopHp` is the most this citizen has been seen at: the world
				// sends current hitpoints and never a maximum, and somebody met
				// already wounded simply starts full and is honest from there.
				int32 Hp = 0;
				if (const FString* Told = Who.Fields.Find(TEXT("health")))
				{
					Hp = FCString::Atoi(**Told);
				}
				View.TopHp = FMath::Max(View.TopHp, Hp);
				if (Hp > 0 && View.TopHp > 0 && Hp < View.TopHp)
				{
					const float Left = static_cast<float>(Hp) / static_cast<float>(View.TopHp);
					const int32 Full = FMath::Clamp(FMath::RoundToInt(Left * 10.f), 0, 10);
					FString Bar;
					for (int32 i = 0; i < 10; ++i) { Bar += (i < Full) ? TEXT("|") : TEXT("."); }
					LabelText += TEXT("\n") + Bar;
				}
				View.Plate->SetWorldLocation(Location + FVector(0.f, 0.f, PlateHeight));
				if (UIntervalPlateWidget* W = Cast<UIntervalPlateWidget>(View.Plate->GetUserWidgetObject()))
				{
					W->Set(LabelText, PlateColour, PlateSize);
					W->Doing(Deed_, PlateSize, bCrowed);
				}
			}
		}
	}

	// Anybody who left view stops being drawn. Their components are kept: a
	// citizen who steps back over a zone edge should not cost a re-spawn.
	for (TPair<FString, FIntervalCitizenView>& Pair : Citizens)
	{
		if (!Pair.Value.bSeenThisFrame)
		{
			if (Pair.Value.Mesh) { Pair.Value.Mesh->SetVisibility(false); }
			if (Pair.Value.Plate) { Pair.Value.Plate->SetVisibility(false); }
		}
		else if (Pair.Value.Mesh && !Pair.Value.Mesh->IsVisible())
		{
			Pair.Value.Mesh->SetVisibility(true);
		}
	}
}

const TMap<FName, FIntervalPropKind>& AIntervalCitizens::Bestiary() const
{
	const UIntervalLook* Chosen = UIntervalLook::Resolve(Look);
	return (Chosen && Chosen->Mobs.Num() > 0) ? Chosen->Mobs : Mobs;
}

void AIntervalCitizens::UpdateBeasts(float Alpha, float DeltaSeconds,
	const FVector& ViewLocation)
{
	const FIntervalFrame& Now = Bridge->GetFrame();
	const FIntervalFrame& Was = Bridge->GetPreviousFrame();

	// ---- THE ONES WITH SKELETONS ----
	// A beast that walks and fights is worth a component of its own. It reads
	// its verb the same way a citizen does, out of the same table -- the world
	// says nothing about what a mob is DOING, so what there is to go on is
	// whether it moved and whether it is still alive, and both of those are
	// the window's own reading rather than the world's word.
	for (TPair<FString, FIntervalCitizenView>& Pair : BeastViews)
	{
		Pair.Value.bSeenThisFrame = false;
	}
	for (const TPair<FString, FIntervalEntity>& Pair : Now.Mobs)
	{
		const FIntervalEntity& Mob = Pair.Value;
		const FIntervalPropKind* Kind = Bestiary().Find(MobKey(Mob));
		if (!Kind || !Kind->Skeletal)
		{
			continue;
		}
		FIntervalCitizenView& View = BeastViews.FindOrAdd(Pair.Key);
		if (!View.Mesh)
		{
			USkeletalMeshComponent* Skin = NewObject<USkeletalMeshComponent>(this);
			Skin->SetupAttachment(RootComponent);
			Skin->SetMobility(EComponentMobility::Movable);
			Skin->SetSkeletalMesh(Kind->Skeletal);
			Skin->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Skin->SetAnimInstanceClass(UIntervalAnimInstance::StaticClass());
			Skin->SetAnimationMode(EAnimationMode::AnimationBlueprint);
			// EVERY SLOT, NOT THE FIRST. These figures are modular -- skin, hair,
			// eyes and outfit are separate slots on one mesh -- so painting slot
			// zero gave a wraith in a mossy shirt with a citizen's face still on
			// it. A material named for a MOB is the whole creature's colour: that
			// is what naming one means, and nothing that has a material today
			// wanted only part of itself painted.
			if (Kind->Material)
			{
				for (int32 Slot = 0; Slot < Skin->GetNumMaterials(); ++Slot)
				{
					Skin->SetMaterial(Slot, Kind->Material);
				}
			}
			Skin->RegisterComponent();

			// AND WHAT IT IS WEARING.
			//
			// Every humanoid in the bestiary -- the risen, the gibbet king,
			// the five faces an incursion wears -- is the citizens' own body,
			// and that body is a BARE one: the outfit is a separate mesh that
			// follows its pose. Drawn without one, a barrow-wight is a naked
			// bodybuilder in briefs walking across a moor, which is what the
			// first contact sheet of the bestiary showed.
			//
			// Same leader-and-follower as a citizen and a keeper: the part is
			// attached to the LEADER rather than the actor, or it takes its
			// bounds from the actor's origin and is culled the moment the
			// camera looks away from it.
			for (const TObjectPtr<USkeletalMesh>& Part : Kind->SkeletalParts)
			{
				if (!Part) { continue; }
				USkeletalMeshComponent* Piece = NewObject<USkeletalMeshComponent>(this);
				Piece->SetupAttachment(Skin);
				Piece->SetMobility(EComponentMobility::Movable);
				Piece->SetSkeletalMesh(Part.Get());
				Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				if (Kind->Material)
				{
					for (int32 Slot = 0; Slot < Piece->GetNumMaterials(); ++Slot)
					{
						Piece->SetMaterial(Slot, Kind->Material);
					}
				}
				Piece->RegisterComponent();
				Piece->AttachToComponent(Skin,
					FAttachmentTransformRules::SnapToTargetIncludingScale);
				Piece->SetLeaderPoseComponent(Skin);
				Piece->SetBoundsScale(2.f);
				View.Limbs.Add(Piece);
			}
			View.Mesh = Skin;
			// STANDING, ON THE VERY FIRST FRAME. A creature built this tick
			// and told nothing until the next one is a creature seen once, by
			// everybody, in its bind pose.
			PlayBeast(Skin, *Kind, TEXT("still"), Pair.Key, 0.f);
			View.Verb = TEXT("still");
		}
		View.bSeenThisFrame = true;

		FVector Location;
		bool bMoving = false;
		DrawnPosition(Pair.Key, Mob, Was.Mobs, Alpha, Now.Tick, Location, bMoving);
		Location.Z += Kind->ZOffset;
		if (bMoving)
		{
			if (const FIntervalEntity* From = Was.Mobs.Find(Pair.Key))
			{
				View.Yaw = FMath::RadiansToDegrees(FMath::Atan2(
					static_cast<float>(Mob.Y - From->Y), static_cast<float>(Mob.X - From->X)));
			}
		}
		// IT TURNS, IT DOES NOT SNAP. See FIntervalCitizenView::YawShown.
		// A beast turns more slowly than a person: a wolf swinging its whole
		// body round in a tenth of a second reads as a glitch, and at three
		// hundred degrees a second it reads as an animal.
		View.YawShown = View.bYawKnown
			? FMath::FixedTurn(View.YawShown, View.Yaw, 300.f * DeltaSeconds)
			: View.Yaw;
		View.bYawKnown = true;

		// THE LEAN FIRST, THEN THE TURN. Composing the other way round spins
		// a creature about the axis it is lying on instead of about its feet.
		View.Mesh->SetWorldLocationAndRotation(Location,
			(FRotator(0.f, View.YawShown, 0.f).Quaternion() * Kind->Lean.Quaternion()).Rotator());
		View.Mesh->SetWorldScale3D(Kind->Scale);

		// §7ca: and what it just took. A beast has no blow list of its own --
		// `blows` is a citizen's record of a flurry they received -- so this is
		// always the single honest difference, which is all a beast ever needs.
		SplatsFor(View, Mob, Location, false);

		// ---- WHAT A FIGHT LOOKS LIKE FROM OUTSIDE IT ----
		//
		// A fight showed NOTHING. Two figures stood next to each other and one
		// of them eventually fell over; whether a blow had landed, whether the
		// thing was nearly dead, whether you were winning -- none of it was on
		// screen, and the only way to follow a fight was to read the socket.
		//
		// Shown only on a creature that has been HURT. A plate over every
		// sheep and crow on the island would be a HUD, and this window is a
		// window: the world is the thing being looked at, not the numbers.
		// Hurt is the one state where the number is what you need.
		{
			int32 Hp = 0;
			if (const FString* Told = Mob.Fields.Find(TEXT("health")))
			{
				Hp = FCString::Atoi(**Told);
			}
			View.TopHp = FMath::Max(View.TopHp, Hp);
			const bool bHurt = Hp > 0 && View.TopHp > 0 && Hp < View.TopHp;
			if (bHurt && !View.Plate)
			{
				UWidgetComponent* Plate = NewObject<UWidgetComponent>(this);
				Plate->SetupAttachment(RootComponent);
				Plate->SetMobility(EComponentMobility::Movable);
				Plate->SetWidgetSpace(EWidgetSpace::Screen);
				Plate->SetWidgetClass(UIntervalPlateWidget::StaticClass());
				Plate->SetDrawSize(FVector2D(220.f, 34.f));
				Plate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Plate->RegisterComponent();
				View.Plate = Plate;
			}
			if (View.Plate)
			{
				const bool bNear = PlateMaxDistance <= 0.f
					|| FVector::DistSquared(Location, ViewLocation)
					   < PlateMaxDistance * PlateMaxDistance;
				View.Plate->SetVisibility(bHurt && bNear);
				if (bHurt && bNear)
				{
					const float Left = static_cast<float>(Hp) / static_cast<float>(View.TopHp);
					// Ten notches, which reads as a bar without being one, and
					// stays legible at the distance this camera actually sits.
					const int32 Full = FMath::Clamp(FMath::RoundToInt(Left * 10.f), 0, 10);
					FString Bar;
					for (int32 i = 0; i < 10; ++i) { Bar += (i < Full) ? TEXT("|") : TEXT("."); }
					// Green while it is winning, red as it goes -- the same
					// reading a person makes of a wound without being told.
					const FLinearColor Blood = FMath::Lerp(
						FLinearColor(0.86f, 0.24f, 0.18f),
						FLinearColor(0.42f, 0.78f, 0.34f), Left);
					View.Plate->SetWorldLocation(Location + FVector(0.f, 0.f, PlateHeight * 0.8f));
					if (UIntervalPlateWidget* W = Cast<UIntervalPlateWidget>(
						View.Plate->GetUserWidgetObject()))
					{
						W->Set(Bar, Blood, PlateSize * 0.9f);
					}
				}
			}
		}

		// ITS OWN CLIPS, NOT THE CITIZENS'. `PlayVerb` reads the wardrobe's
		// table, which is authored for the citizens' skeleton; a wolf will
		// not take one, and asking used to leave it in its bind pose. The
		// creature's row carries its own.
		//
		// CALLED EVERY FRAME, not only when the verb changes. Asking for the
		// clip that is already arriving is a no-op inside `CrossFade` except
		// for one thing: it updates the rate. That is what lets a creature
		// slow its legs down as it slows down, rather than only when it stops.
		// ---- AND A BEAST THAT IS SWINGING IS FIGHTING ----
		//
		// THE SAME FAULT AS THE SPELLS, in the other half of the bestiary.
		// `VerbFor` reads `deed` and then `action.type`, and a mob has
		// NEITHER: the engine's own field list for a mob is health, position,
		// the marks on it, and `lastSwing`. So the question "what is this
		// creature doing" had no field to answer it, every beast fell through
		// to walk or still, and the attack clip in every creature's row was
		// unreachable from the first day it was imported. The spider has a
		// perfectly good `fight` motion and has never once played it.
		//
		// What the world DOES record is the interval it last swung on, which
		// is the fact rather than the intention, exactly as `stilledUntil` is
		// for a spell. One interval of grace because a frame can land either
		// side of the tick that wrote it.
		//
		// `fight` is the beast table's own word for it (parts.py, BEAST_VERB),
		// and it stays the beast table's word: the citizens' verb is `attack`
		// and these are different vocabularies for different skeletons.
		FName Verb = VerbFor(Mob, bMoving, INDEX_NONE);
		if (Verb != TEXT("felled"))
		{
			if (const FString* Swung = Mob.Fields.Find(TEXT("lastSwing")))
			{
				const int32 At = FCString::Atoi(**Swung);
				if (At > 0 && Now.Tick - At <= 1 && Kind->Motions.Contains(TEXT("fight")))
				{
					Verb = TEXT("fight");
				}
			}
		}
		View.Verb = Verb;
		PlayBeast(View.Mesh, *Kind, Verb, Pair.Key,
			GroundSpeed(Mob, Was.Mobs.Find(Pair.Key),
				Bridge ? Bridge->GetTickSeconds() : 1.f));
	}
	for (TPair<FString, FIntervalCitizenView>& Pair : BeastViews)
	{
		if (Pair.Value.Mesh)
		{
			// A beast the world stopped mentioning is hidden, not destroyed:
			// respawns come back under the same id and a component kept is a
			// component not rebuilt every time something is killed.
			//
			// AND ITS CLOTHES WITH IT. Visibility does not reach a child
			// component unless it is told to, so a hidden wight left its
			// outfit standing on the moor.
			Pair.Value.Mesh->SetVisibility(Pair.Value.bSeenThisFrame, true);
		}
	}

	for (const TPair<FName, TArray<FString>>& Pair : BeastOrder)
	{
		TObjectPtr<UInstancedStaticMeshComponent>* Found = BeastPools.Find(Pair.Key);
		UInstancedStaticMeshComponent* Pool = Found ? Found->Get() : nullptr;
		if (!Pool || Pool->GetInstanceCount() != Pair.Value.Num())
		{
			continue;
		}
		const FIntervalPropKind* Kind = Bestiary().Find(Pair.Key);
		if (!Kind)
		{
			continue;
		}

		TArray<FTransform> Transforms;
		Transforms.Reserve(Pair.Value.Num());
		for (const FString& Id : Pair.Value)
		{
			const FIntervalEntity* Mob = Now.Mobs.Find(Id);
			if (!Mob)
			{
				Transforms.Add(FTransform(FVector(0.f, 0.f, -100000.f)));   // off the world until the cast is rebuilt
				continue;
			}
			FVector Location;
			bool bMoving = false;
			DrawnPosition(Id, *Mob, Was.Mobs, Alpha, Now.Tick, Location, bMoving);
			Location.Z += Kind->ZOffset;

			float Yaw = 0.f;
			if (bMoving)
			{
				if (const FIntervalEntity* From = Was.Mobs.Find(Id))
				{
					Yaw = FMath::RadiansToDegrees(FMath::Atan2(
						static_cast<float>(Mob->Y - From->Y), static_cast<float>(Mob->X - From->X)));
				}
			}
			Transforms.Add(FTransform(
				(FRotator(0.f, Yaw, 0.f).Quaternion() * Kind->Lean.Quaternion()).Rotator(),
				Location, Kind->Scale));
		}
		Pool->BatchUpdateInstancesTransforms(0, Transforms, true, true, false);
	}
}

void AIntervalCitizens::Tick(float DeltaSeconds)
{
	// §7ca: the numbers rise and fade on the FRAME, not on the interval. A
	// splat that moved once a second would be the staircase the sun used to
	// climb, and for the same reason: the world's clock is a tick and
	// everything between two ticks is this window's own work.
	DriveSplats();

	Super::Tick(DeltaSeconds);
	if (!Bridge || Bridge->GetFrame().Tick == 0)
	{
		return;
	}

	// 0 at the interval just received, 1 at the next one due. THIS NUMBER IS
	// COSMETIC. It is read here, used to place drawings, and discarded. It is
	// never written back into an entity, never rounded to a tile, and never
	// reaches SendIntent.
	const float Alpha = FMath::Clamp(Bridge->GetInterpAlpha(), 0.f, 1.f);

	// Where the camera that actually rendered last frame was standing. This is
	// the one view location runtime code can see in BOTH play and simulate,
	// which matters because every screenshot of this window is taken in
	// simulate. When there is no such camera -- the first frame, or a headless
	// run -- there is no distance to test against, and the honest answer is to
	// draw the plate rather than to treat everyone as infinitely far away.
	// Leaving the fallback at the origin silently hid every name plate on the
	// island, which looked exactly like the text component not working.
	FVector ViewLocation = FVector::ZeroVector;
	bool bHaveView = false;
	if (UWorld* World = GetWorld())
	{
		if (World->ViewLocationsRenderedLastFrame.Num() > 0)
		{
			ViewLocation = World->ViewLocationsRenderedLastFrame[0];
			bHaveView = true;
		}
	}

	static bool bSaidView = false;
	if (!bSaidView)
	{
		bSaidView = true;
		UE_LOG(LogIntervalCitizens, Log, TEXT("view location %s"),
			bHaveView ? TEXT("available (plates will face the camera)")
			          : TEXT("NOT available (plates keep their world rotation)"));
	}

	UpdatePeople(Alpha, ViewLocation, bHaveView, DeltaSeconds);
	UpdateBeasts(Alpha, DeltaSeconds, ViewLocation);
}
