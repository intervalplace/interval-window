// Copyright interval.

#include "IntervalPanel.h"
#include "IntervalMenu.h"
#include "IntervalHud.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "IntervalBridgeSubsystem.h"
#include "IntervalHand.h"
#include "IntervalGate.h"
#include "IntervalTypes.h"
#include "EngineUtils.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
	// The panel's own palette: parchment on a dark ground, one warm accent.
	// Deliberately the gate's colours -- a window whose door and whose panel
	// disagree about what it is made of reads as two programs.
	const FLinearColor Ink(0.86f, 0.83f, 0.74f, 1.f);
	const FLinearColor Faint(0.52f, 0.50f, 0.46f, 1.f);
	const FLinearColor Warm(0.85f, 0.66f, 0.36f, 1.f);
	const FLinearColor Refused(0.88f, 0.44f, 0.34f, 1.f);
	const FLinearColor Ground(0.04f, 0.04f, 0.045f, 0.82f);

	/** A number the world sent, which arrives as a string like every field. */
	int32 Num(const FIntervalEntity& Who, const TCHAR* Key, int32 Fallback = 0)
	{
		if (const FString* Found = Who.Fields.Find(Key))
		{
			return FCString::Atoi(**Found);
		}
		return Fallback;
	}

	/** A nested object or array arrives as the raw JSON the world sent. */
	TSharedPtr<FJsonValue> Json(const FIntervalEntity& Who, const TCHAR* Key)
	{
		const FString* Raw = Who.Fields.Find(Key);
		if (!Raw || Raw->IsEmpty() || *Raw == TEXT("null"))
		{
			return nullptr;
		}
		TSharedPtr<FJsonValue> Value;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
		return FJsonSerializer::Deserialize(Reader, Value) ? Value : nullptr;
	}
}

UIntervalPanelWidget::UIntervalPanelWidget(const FObjectInitializer& Init)
	: Super(Init)
{
	// It has to take the keyboard for Tab to reach it, and it must not take
	// the mouse: the hand's click-to-walk is underneath, and a panel that
	// swallowed clicks would make the world unreachable.
	bIsFocusable = true;
}

UTextBlock* UIntervalPanelWidget::Line(UVerticalBox* Into, const FLinearColor& Tint,
	int32 Size, bool bBold)
{
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = Size;
	Font.TypefaceFontName = bBold ? TEXT("Bold") : TEXT("Regular");
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(Tint));
	if (UVerticalBoxSlot* Slot = Cast<UVerticalBoxSlot>(Into->AddChild(Text)))
	{
		Slot->SetPadding(FMargin(0.f, 1.f));
	}
	return Text;
}

TSharedRef<SWidget> UIntervalPanelWidget::RebuildWidget()
{
	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	// ---- THE COLUMN: what you have ----
	Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Frame->SetBrushColor(Ground);
	Frame->SetPadding(FMargin(14.f, 12.f));
	Column = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Frame->SetContent(Column);

	Line(Column, Warm, 13, true)->SetText(FText::FromString(TEXT("CARRIED")));
	PurseRow = Line(Column, Ink, 12, false);
	BodyRow = Line(Column, Ink, 12, false);
	DoingRow = Line(Column, Faint, 11, false);
	HoursRow = Line(Column, Faint, 11, false);
	HaulRow = Line(Column, Warm, 11, false);

	Line(Column, Faint, 10, false)->SetText(FText::FromString(TEXT(" ")));
	Line(Column, Warm, 11, true)->SetText(FText::FromString(TEXT("PACK")));
	const int32 Slots = Owner ? FMath::Max(1, Owner->PackSlots) : 12;
	for (int32 i = 0; i < Slots; ++i)
	{
		PackRows.Add(Line(Column, Ink, 11, false));
	}

	Line(Column, Faint, 10, false)->SetText(FText::FromString(TEXT(" ")));
	Line(Column, Warm, 11, true)->SetText(FText::FromString(TEXT("WORN")));
	const int32 Gear = Owner ? Owner->WornOrder.Num() : 5;
	for (int32 i = 0; i < Gear; ++i)
	{
		WornRows.Add(Line(Column, Ink, 11, false));
	}

	Line(Column, Faint, 10, false)->SetText(FText::FromString(TEXT(" ")));
	Line(Column, Warm, 11, true)->SetText(FText::FromString(TEXT("LEARNED")));
	SkillRow = Line(Column, Ink, 11, false);

	Line(Column, Faint, 10, false)->SetText(FText::FromString(TEXT(" ")));
	BookRow = Line(Column, Warm, 11, true);
	const int32 Most = Owner
		? FMath::Max(Owner->CommonBook.Num(), Owner->BarrowBook.Num()) : 7;
	for (int32 i = 0; i < Most; ++i)
	{
		SpellRows.Add(Line(Column, Ink, 11, false));
	}

	if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Frame))
	{
		Slot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 0.f));
		Slot->SetPosition(FVector2D(24.f, 24.f));
		Slot->SetAutoSize(true);
	}

	// ---- THE FEED: what the world said ----
	//
	// It was a debug draw on the screen -- a stand-in, in its own words. The
	// feed is the only channel a refusal has, and a refusal that looks like
	// engine spew is a refusal nobody reads.
	FeedFrame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	FeedFrame->SetBrushColor(Ground);
	FeedFrame->SetPadding(FMargin(14.f, 10.f));
	FeedColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	FeedFrame->SetContent(FeedColumn);
	for (int32 i = 0; i < 6; ++i)
	{
		FeedRows.Add(Line(FeedColumn, Ink, 12, false));
	}
	if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(FeedFrame))
	{
		Slot->SetAnchors(FAnchors(0.f, 1.f, 0.f, 1.f));
		Slot->SetAlignment(FVector2D(0.f, 1.f));
		Slot->SetPosition(FVector2D(24.f, -24.f));
		Slot->SetAutoSize(true);
	}

	return Super::RebuildWidget();
}

FReply UIntervalPanelWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Key)
{
	if (Key.GetKey() == EKeys::Tab)
	{
		// Refresh() applies it, so the door's own answer is never overridden.
		bShown = !bShown;
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(Geometry, Key);
}

void UIntervalPanelWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
	Super::NativeTick(Geometry, DeltaSeconds);
	Refresh();
}

void UIntervalPanelWidget::Refresh()
{
	if (!Bridge || !Owner)
	{
		return;
	}

	// NOT WHILE THE DOOR IS SHUT. The gate is a title card: the world's name,
	// the theme, and one button. A list of an empty pack lying across the
	// corner of it is the exact thing a title card is for NOT having.
	const bool bDoorShut = Owner->Gate && Owner->Gate->IsWaiting();
	const ESlateVisibility Want = (bShown && !bDoorShut)
		? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
	if (Frame && Frame->GetVisibility() != Want) { Frame->SetVisibility(Want); }
	if (FeedFrame && FeedFrame->GetVisibility() != Want) { FeedFrame->SetVisibility(Want); }
	if (bDoorShut)
	{
		return;
	}
	const FIntervalFrame& Frame_ = Bridge->GetFrame();

	// THE FEED EVERY TICK, the rest only when the world has moved on. A pack
	// cannot change between intervals -- the world is a ledger of deeds and a
	// deed lands on a tick -- so rebuilding these strings sixty times a second
	// would be sixty times the work for one answer.
	if (Owner->Hand)
	{
		const TArray<FIntervalFeedLine>& Said = Owner->Hand->GetFeed();
		for (int32 i = 0; i < FeedRows.Num(); ++i)
		{
			const int32 From = Said.Num() - FeedRows.Num() + i;
			if (!FeedRows[i]) { continue; }
			if (Said.IsValidIndex(From))
			{
				FeedRows[i]->SetText(FText::FromString(Said[From].Text));
				FeedRows[i]->SetColorAndOpacity(FSlateColor(
					Said[From].bRefusal ? Refused : Ink));
			}
			else
			{
				FeedRows[i]->SetText(FText::GetEmpty());
			}
		}
	}

	if (Frame_.Tick == DrawnAt)
	{
		return;
	}
	DrawnAt = Frame_.Tick;

	if (!Frame_.bHasMe)
	{
		if (PurseRow) { PurseRow->SetText(FText::FromString(TEXT("not in the world yet"))); }
		return;
	}
	const FIntervalEntity& Me = Frame_.Me;

	const FString* Called = Me.Fields.Find(TEXT("name"));
	const FString Who = (Called && !Called->IsEmpty() && *Called != TEXT("null"))
		? *Called : FString(TEXT("unnamed"));
	if (PurseRow)
	{
		PurseRow->SetText(FText::FromString(FString::Printf(
			TEXT("%s, %d gold"), *Who, Num(Me, TEXT("gold")))));
	}
	if (BodyRow)
	{
		BodyRow->SetText(FText::FromString(FString::Printf(
			TEXT("%d health, standing at %d, %d"), Num(Me, TEXT("health")), Me.X, Me.Y)));
	}
	if (DoingRow)
	{
		const FString* Doing = Me.Fields.Find(TEXT("action"));
		DoingRow->SetText(FText::FromString(
			(Doing && !Doing->IsEmpty() && *Doing != TEXT("null"))
			? FString::Printf(TEXT("doing: %s"), **Doing) : FString(TEXT("idle"))));
	}

	// ---- A CONSIGNMENT, WHICH THE WINDOW COULD NOT SEE AT ALL ----
	//
	// Taking one up moves goods OUT of the pack into a container with a route
	// of towns to carry it along -- and until this line existed a citizen
	// hauling five slots across the island was drawn exactly like one
	// carrying nothing. The pack simply emptied and nothing said where the
	// goods had gone, which reads as having lost them.
	//
	// The route is the world's: `from`, an ordered list of towns and which
	// leg is current. Shown as the NEXT town rather than the whole list,
	// because what a hauler needs is where to walk to, and the rest is on the
	// road behind them.
	if (HaulRow)
	{
		const FString* Load = Me.Fields.Find(TEXT("consignment"));
		bool bDrewHaul = false;
		if (Load && !Load->IsEmpty() && *Load != TEXT("null"))
		{
			TSharedPtr<FJsonObject> Carried;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Load);
			if (FJsonSerializer::Deserialize(Reader, Carried) && Carried.IsValid())
			{
				int32 Held = 0;
				const TArray<TSharedPtr<FJsonValue>>* Items = nullptr;
				if (Carried->TryGetArrayField(TEXT("items"), Items) && Items)
				{
					for (const TSharedPtr<FJsonValue>& V : *Items)
					{
						if (V.IsValid() && V->Type != EJson::Null) { ++Held; }
					}
				}
				FString Next;
				const TArray<TSharedPtr<FJsonValue>>* Route = nullptr;
				int32 Leg = 0;
				Carried->TryGetNumberField(TEXT("leg"), Leg);
				if (Carried->TryGetArrayField(TEXT("route"), Route) && Route
					&& Route->IsValidIndex(Leg) && (*Route)[Leg].IsValid())
				{
					Next = (*Route)[Leg]->AsString();
					// The world names a town by the id of a thing standing in
					// it -- "plan-norwick-163". The town is the middle word,
					// and that is the part a hauler is actually walking to.
					TArray<FString> Parts;
					Next.ParseIntoArray(Parts, TEXT("-"));
					if (Parts.Num() >= 2) { Next = Parts[1]; }
				}
				HaulRow->SetText(FText::FromString(Next.IsEmpty()
					? FString::Printf(TEXT("hauling %d for delivery"), Held)
					: FString::Printf(TEXT("hauling %d  ->  %s"), Held, *Next)));
				bDrewHaul = true;
			}
		}
		if (!bDrewHaul) { HaulRow->SetText(FText::GetEmpty()); }
	}

	// ---- CLOSING TIME ----
	//
	// Drawn always, not only when it runs out, because it counts PRESENCE: it
	// falls while a citizen stands in a meadow doing nothing, so the first
	// sign of it must not BE running out. The world hands us its own warning
	// band rather than a number chosen here, and being stood down is said in
	// as many words -- a citizen whose deeds have quietly stopped landing is
	// owed a reason on screen, not a mystery to debug.
	if (HoursRow)
	{
		const FIntervalFrame& F = Frame_;
		if (F.CeilingAllow <= 0)
		{
			HoursRow->SetText(FText::GetEmpty());
		}
		else if (F.bStoodDown)
		{
			HoursRow->SetColorAndOpacity(FSlateColor(Refused));
			HoursRow->SetText(FText::FromString(
				TEXT("stood down: present, but the world will not take a deed yet")));
		}
		else
		{
			const int32 Mins = F.CeilingLeft / 60;
			const bool bNearly = F.CeilingLeft <= F.CeilingWarn;
			HoursRow->SetColorAndOpacity(FSlateColor(bNearly
				? FLinearColor(0.85f, 0.55f, 0.20f) : Faint));
			HoursRow->SetText(FText::FromString(bNearly
				? FString::Printf(TEXT("%d min left of the day, nearly stood down"), Mins)
				: FString::Printf(TEXT("%d min left of the day"), Mins)));
		}
	}

	// ---- THE PACK ----
	// An array of twelve, each entry either null or {item, qty}. The slot
	// NUMBER is shown because it is what every deed names: `wield 3` means the
	// third slot, and a panel that hides the number makes its own verbs
	// unusable.
	TSharedPtr<FJsonValue> Pack = Json(Me, TEXT("inventory"));
	const TArray<TSharedPtr<FJsonValue>>* Entries = nullptr;
	if (Pack.IsValid()) { Pack->TryGetArray(Entries); }
	for (int32 i = 0; i < PackRows.Num(); ++i)
	{
		if (!PackRows[i]) { continue; }
		FString Says = FString::Printf(TEXT("%2d  ."), i);
		FLinearColor Tint = Faint;
		if (Entries && Entries->IsValidIndex(i) && (*Entries)[i].IsValid()
			&& (*Entries)[i]->Type == EJson::Object)
		{
			const TSharedPtr<FJsonObject>& Slot = (*Entries)[i]->AsObject();
			FString Item;
			double Qty = 1.0;
			Slot->TryGetStringField(TEXT("item"), Item);
			Slot->TryGetNumberField(TEXT("qty"), Qty);
			if (!Item.IsEmpty())
			{
				Says = (Qty > 1.0)
					? FString::Printf(TEXT("%2d  %s ×%d"), i, *Item, static_cast<int32>(Qty))
					: FString::Printf(TEXT("%2d  %s"), i, *Item);
				Tint = Ink;
			}
		}
		PackRows[i]->SetText(FText::FromString(Says));
		PackRows[i]->SetColorAndOpacity(FSlateColor(Tint));
	}

	// ---- WHAT IS WORN ----
	TSharedPtr<FJsonValue> Gear = Json(Me, TEXT("equipment"));
	const TSharedPtr<FJsonObject>* Worn = nullptr;
	if (Gear.IsValid()) { Gear->TryGetObject(Worn); }
	for (int32 i = 0; i < WornRows.Num(); ++i)
	{
		if (!WornRows[i] || !Owner->WornOrder.IsValidIndex(i)) { continue; }
		const FString& Where = Owner->WornOrder[i];
		FString What = TEXT("..");
		FLinearColor Tint = Faint;
		if (Worn)
		{
			// THE SLOT HOLDS A STACK. {"item":"iron-hatchet","qty":1}, the
			// same shape as an inventory slot -- so asking for a string here
			// failed on every slot and the whole block read as bare. A
			// citizen who had just wielded a hatchet was shown wearing
			// nothing. The bare-string form is still read, in case the world
			// ever sends one.
			FString Held;
			const TSharedPtr<FJsonObject>* Stack = nullptr;
			if ((*Worn)->TryGetObjectField(Where, Stack) && Stack)
			{
				(*Stack)->TryGetStringField(TEXT("item"), Held);
			}
			else
			{
				(*Worn)->TryGetStringField(Where, Held);
			}
			if (!Held.IsEmpty())
			{
				What = Held;
				Tint = Ink;
			}
		}
		WornRows[i]->SetText(FText::FromString(
			FString::Printf(TEXT("%-8s %s"), *Where, *What)));
		WornRows[i]->SetColorAndOpacity(FSlateColor(Tint));
	}

	// ---- WHAT IS KNOWN ----
	// Only the skills that have moved. Nine zeroes is nine lines saying the
	// same nothing, and a freshly born citizen has nine of them.
	TSharedPtr<FJsonValue> Learned = Json(Me, TEXT("skills"));
	const TSharedPtr<FJsonObject>* Craft = nullptr;
	if (Learned.IsValid()) { Learned->TryGetObject(Craft); }
	FString Known;
	if (Craft)
	{
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Craft)->Values)
		{
			const int32 At = Pair.Value.IsValid() ? static_cast<int32>(Pair.Value->AsNumber()) : 0;
			if (At > 0)
			{
				if (!Known.IsEmpty()) { Known += TEXT("  "); }
				Known += FString::Printf(TEXT("%s %d"), *Pair.Key, At);
			}
		}
	}
	if (SkillRow)
	{
		SkillRow->SetText(FText::FromString(Known.IsEmpty()
			? TEXT("no craft practised yet") : Known));
		SkillRow->SetColorAndOpacity(FSlateColor(Known.IsEmpty() ? Faint : Ink));
	}
	// ---- THE SPELLBOOK ----
	//
	// WHICH BOOK, from the world. A citizen speaks the common book unless they
	// have turned at an ossuary, and the two are disjoint -- so this shows the
	// one they have, not both. Whether they can spend a sigil on any given
	// spell today is the world's question and comes back as a refusal.
	const FString* Book = Me.Fields.Find(TEXT("book"));
	const bool bBarrow = Book && *Book == TEXT("barrow");
	const TArray<FString>& Speaks = bBarrow ? Owner->BarrowBook : Owner->CommonBook;
	if (BookRow)
	{
		BookRow->SetText(FText::FromString(bBarrow
			? TEXT("THE BARROW BOOK") : TEXT("THE COMMON BOOK")));
	}
	for (int32 i = 0; i < SpellRows.Num(); ++i)
	{
		if (!SpellRows[i]) { continue; }
		SpellRows[i]->SetText(FText::FromString(
			Speaks.IsValidIndex(i) ? Speaks[i] : FString()));
	}
}

AIntervalPanel::AIntervalPanel()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AIntervalPanel::BeginPlay()
{
	Super::BeginPlay();
	if (!bShowPanel)
	{
		return;
	}
	// NOTHING WITHOUT A PLAYER CONTROLLER. Simulate has none -- every
	// photograph in these notes is taken there -- and a widget added to a
	// viewport that does not exist is a crash, not an empty screen.
	APlayerController* Who = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!Who)
	{
		return;
	}
	UIntervalBridgeSubsystem* Found = GetGameInstance()
		? GetGameInstance()->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	Widget = CreateWidget<UIntervalPanelWidget>(Who, UIntervalPanelWidget::StaticClass());
	if (!Widget)
	{
		return;
	}
	// The one hand in the level. `TActorIterator` and a break reads as a loop
	// that never loops to the compiler, which this project treats as an error.
	TActorIterator<AIntervalHand> Found_(GetWorld());
	Hand = Found_ ? *Found_ : nullptr;
	TActorIterator<AIntervalGate> Door_(GetWorld());
	Gate = Door_ ? *Door_ : nullptr;
	Widget->Bridge = Found;
	Widget->Owner = this;
	// UNDER EVERYTHING ELSE. The gate sits at zero and must cover this; a
	// panel drawn over the door would be a list of an empty pack in front of
	// the world's name.
	Widget->AddToViewport(-10);

	// THE HUD AND THE MENU USED TO BE SPAWNED HERE, and both have moved to
	// `AIntervalHand`, which is the one actor that is always present when a
	// citizen is. Leaving them here made the entire interface a dependent of
	// this overlay: switching the overlay off took the chat, the pack, the
	// tabs and the right-click menu with it. See the note in the hand.
}

void AIntervalPanel::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Widget)
	{
		Widget->RemoveFromParent();
		Widget = nullptr;
	}
	Super::EndPlay(Reason);
}
