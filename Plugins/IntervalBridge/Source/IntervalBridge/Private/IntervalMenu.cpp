// Copyright interval.

#include "IntervalMenu.h"
#include "IntervalTypes.h"

#include "IntervalHand.h"
#include "IntervalBridgeSubsystem.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "Blueprint/WidgetLayoutLibrary.h"

// UNIQUE NAMES, BECAUSE A UNITY BUILD HAS NO FILE SCOPE.
//
// Unreal pastes several .cpp files into one translation unit, and an anonymous
// namespace in one of them is the SAME namespace as the anonymous namespace in
// the next. Five of these files called a colour Ink, three called one Quiet and
// one Ember, two an Oak and a Band, and the module stopped building the moment
// two of them landed in the same blob. Which files share a blob is UBT's
// business and changes between builds, so this is not a thing to fix by moving
// the collision somewhere else: the names are unique now and stay unique.
namespace
{
	// ---- THE SAME BOARD AS EVERYTHING ELSE ----
	//
	// This menu was written before the interface had a material and kept its
	// own colours after the panels got one, so a right click put a flat grey
	// slab with square corners on top of a window made of ink boards with
	// gold rules and rounded edges -- which was noticed the moment the two
	// were on screen together: "the right click menu should match the panels,
	// now it doesn't."
	//
	// So the numbers below are the HUD's, copied deliberately rather than
	// shared through a header: this module does not depend on the HUD and
	// should not start to for the sake of four colours. If the palette moves,
	// both move, and a screenshot says at once whether they still agree.
	const FLinearColor MenuInk(0.90f, 0.87f, 0.78f, 1.f);        // what is written
	const FLinearColor MenuQuiet(0.62f, 0.55f, 0.43f, 1.f);      // the same ink, older
	const FLinearColor MenuEmber(0.90f, 0.58f, 0.24f, 1.f);      // the default line
	const FLinearColor MenuOak(0.038f, 0.040f, 0.052f, 0.94f);   // the board
	const FLinearColor MenuBand(0.52f, 0.40f, 0.17f, 0.85f);     // the one gold rule
	const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
	const FLinearColor Hover(0.86f, 0.62f, 0.28f, 0.22f);    // firelight on a hover

	/**
	 * A brush with the corners taken off, AND ITS COLOUR.
	 *
	 * Both, because a rounded brush is filled from the brush's own TintColor
	 * and not from the border's BrushColor -- set only the second and the
	 * panel comes out white.
	 */
	void Round(FSlateBrush& Brush, float Radius, const FLinearColor& Tint)
	{
		Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
		Brush.OutlineSettings.CornerRadii = FVector4(Radius, Radius, Radius, Radius);
		Brush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
		Brush.TintColor = FSlateColor(Tint);
	}
}

// ---------------------------------------------------------------------------

TSharedRef<SWidget> UIntervalMenuRow::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UButton* Hit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
		FButtonStyle Style = Hit->GetStyle();
		Style.Normal.TintColor = FSlateColor(Clear);
		Style.Hovered.TintColor = FSlateColor(Hover);
		Style.Pressed.TintColor = FSlateColor(Hover);
		Hit->SetStyle(Style);
		Hit->OnClicked.AddDynamic(this, &UIntervalMenuRow::Chosen);

		UTextBlock* Line = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		// THE KEY BECOMES A LABEL HERE AND NOWHERE ELSE. Every option's text
		// passes through this one line on its way to the screen, so this is
		// the right place to take the hyphens out rather than at the forty
		// call sites that build the text. See IntervalName::Spoken.
		Line->SetText(FText::FromString(IntervalName::Spoken(Label)));
		// THE DEFAULT IS THE ONE A LEFT CLICK WOULD HAVE DONE, so it is lit --
		// a menu where every line looks the same makes a player read all of
		// them every time, and the first line is the one they already have.
		Line->SetColorAndOpacity(FSlateColor(bIsDefault ? MenuEmber : MenuInk));
		FSlateFontInfo Font = Line->GetFont();
		Font.Size = 13;
		Line->SetFont(Font);
		if (UButtonSlot* Slot = Cast<UButtonSlot>(Hit->AddChild(Line)))
		{
			Slot->SetPadding(FMargin(10.f, 3.f, 14.f, 3.f));
			Slot->SetHorizontalAlignment(HAlign_Left);
		}
		WidgetTree->RootWidget = Hit;
	}
	return Super::RebuildWidget();
}

void UIntervalMenuRow::Chosen()
{
	// A LINE THAT OPENS A LIST DOES NOT ALSO DO SOMETHING. `fletch` on its
	// own is not a deed -- the world wants to know what into -- and neither
	// is `buy` or `smith`. Choosing one turns the menu into its second page
	// instead of filing anything.
	if (bOpensList && Menu && Hand)
	{
		// AND THE PAGE MAY LEAD TO ANOTHER. `With` carries the answer so far
		// -- for an offer of trade, which slot is being handed over -- so the
		// next page is asked with it and knows what the last one was told.
		const TArray<FIntervalOption> Choices = Hand->ChoicesFor(On, Verb, With);
		if (Choices.Num() > 0)
		{
			Menu->OfferChoices(On, Label, Choices);
			return;
		}
	}
	// A ROW WITH NO VERB IS THERE TO BE READ, not pressed -- the line an
	// empty page puts up to explain itself. Pressing it closes the menu,
	// which is what pressing a sentence should do.
	if (Hand && !Verb.IsEmpty())
	{
		Hand->ActOnWith(Verb, On, With);
	}
	if (Menu)
	{
		Menu->Close();
	}
}

// ---------------------------------------------------------------------------

TSharedRef<SWidget> UIntervalMenuWidget::RebuildWidget()
{
	if (!WidgetTree->RootWidget)
	{
		UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(
			UCanvasPanel::StaticClass());

		// A gold rule round a board of ink: two borders, the same two the
		// panels are made of.
		Plate = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Plate->SetBrushColor(MenuBand);
		Round(Plate->Background, 6.f, MenuBand);
		Plate->SetPadding(FMargin(2.f));
		Plate->SetVisibility(ESlateVisibility::Collapsed);

		UBorder* Inside = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Inside->SetBrushColor(MenuOak);
		Round(Inside->Background, 5.f, MenuOak);
		Inside->SetPadding(FMargin(0.f, 4.f, 0.f, 5.f));

		UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass());

		Head = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Head->SetColorAndOpacity(FSlateColor(MenuQuiet));
		FSlateFontInfo Small = Head->GetFont();
		Small.Size = 11;
		Head->SetFont(Small);
		if (UVerticalBoxSlot* Slot = Column->AddChildToVerticalBox(Head))
		{
			Slot->SetPadding(FMargin(10.f, 1.f, 14.f, 4.f));
		}

		Rows = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Column->AddChildToVerticalBox(Rows);
		Inside->AddChild(Column);
		Plate->AddChild(Inside);

		if (UCanvasPanelSlot* Slot = Root->AddChildToCanvas(Plate))
		{
			Slot->SetAutoSize(true);
		}
		WidgetTree->RootWidget = Root;
	}
	return Super::RebuildWidget();
}

void UIntervalMenuWidget::Close()
{
	if (Plate)
	{
		Plate->SetVisibility(ESlateVisibility::Collapsed);
	}
	if (Rows)
	{
		Rows->ClearChildren();
	}
}

void UIntervalMenuWidget::OfferChoices(const FIntervalTarget& On,
	const FString& Head_, const TArray<FIntervalOption>& Choices)
{
	// THE SECOND PAGE, IN THE SAME PLATE. It does not move: a submenu that
	// jumps somewhere else makes a player look for it, and the thing they
	// just clicked is where their eye already is.
	if (!Plate || !Rows || !Hand)
	{
		return;
	}
	Rows->ClearChildren();
	// THE LINE THEY JUST PRESSED, WORD FOR WORD.
	//
	// This built its own heading out of the verb and the target's name, which
	// reads "buy  lumber" for a stall and "offer_trade  " for a citizen who
	// has not claimed a name -- the world's internal word for the deed and
	// nothing else. The row that opened the page already says what it is in
	// a person's language, and saying it again is the whole job of a heading.
	Head->SetText(FText::FromString(Head_));
	int32 Lines = 0;
	for (const FIntervalOption& Choice : Choices)
	{
		UIntervalMenuRow* Row = CreateWidget<UIntervalMenuRow>(
			GetOwningPlayer(), UIntervalMenuRow::StaticClass());
		if (!Row)
		{
			continue;
		}
		Row->Verb = Choice.Verb;
		Row->With = Choice.Argument;
		Row->bOpensList = Choice.bMore;
		Row->On = On;
		Row->Label = Choice.Label;
		Row->bIsDefault = Lines == 0 && !Choice.Verb.IsEmpty();
		Row->Hand = Hand;
		Row->Menu = this;
		Rows->AddChildToVerticalBox(Row);
		++Lines;
	}
	Plate->SetVisibility(ESlateVisibility::Visible);
}

void UIntervalMenuWidget::Offer(const TArray<FIntervalTarget>& Targets)
{
	if (!Plate || !Rows || !Hand)
	{
		return;
	}
	Close();
	if (Targets.Num() == 0)
	{
		return;
	}

	// EVERYTHING UNDER THE CURSOR, not just the nearest. A wolf standing on a
	// tree's tile does not make the tree unclickable, and a citizen should not
	// have to walk away and come back to chop it.
	int32 Lines = 0;
	for (const FIntervalTarget& Target : Targets)
	{
		for (const FIntervalOption& Option : Hand->OptionsFor(Target))
		{
			// ONE `walk here`, AND ONLY THE LAST ONE. Every target offers it,
			// which on a tile with three things on it is three identical lines.
			if (Option.Verb == TEXT("walk") && &Target != &Targets.Last())
			{
				continue;
			}
			UIntervalMenuRow* Row = CreateWidget<UIntervalMenuRow>(
				GetOwningPlayer(), UIntervalMenuRow::StaticClass());
			if (!Row)
			{
				continue;
			}
			Row->Verb = Option.Verb;
			// A VERB THAT NEEDS A CHOICE AND HAS NOT BEEN GIVEN ONE opens its
			// own list rather than filing a deed with a hole in it. `fletch`
			// with no `make` is refused by the world in as many words --
			// "missing field make on fletch" -- which is the right refusal
			// and the wrong thing to have made a player read.
			Row->bOpensList = Option.Argument.IsEmpty()
				&& Hand->ChoicesFor(Target, Option.Verb).Num() > 0;
			// What the verb is ABOUT, for the verbs that name a thing:
			// `buy iron-pickaxe`. Without this the row filed a purchase of
			// nothing, which the world refuses with no item named.
			Row->With = Option.Argument;
			Row->On = Target;
			Row->Label = Option.Label;
			Row->bIsDefault = Lines == 0;
			Row->Hand = Hand;
			Row->Menu = this;
			Rows->AddChildToVerticalBox(Row);
			++Lines;
		}
	}
	if (Lines == 0)
	{
		return;
	}

	// WHAT THE MENU IS ABOUT, WHICH IS THE THING AND NOT THE MAP REFERENCE.
	//
	// This printed the tile for everything except a pack slot, so a right
	// click on a person gave a menu headed "452, 201" -- and since the line
	// under it reads `trade with Delia` the number looks like a fact about
	// Delia. It was read as one: "on the citizen menu it says standing is
	// 452, 201 and that's just wrong."
	//
	// So anything with a name is named. A citizen gets the same three things
	// their nameplate carries -- name, calling, standing -- because that is
	// what you want to know about somebody before you offer them a trade,
	// and they are read off the frame the bridge already sends. Only bare
	// ground falls back to the tile, which is the one target that genuinely
	// IS a place.
	FString About = Targets[0].Name;
	if (Targets[0].Kind == EIntervalTargetKind::Citizen && Bridge)
	{
		if (const FIntervalEntity* Who = Bridge->GetFrame().Players.Find(Targets[0].Id))
		{
			if (const FString* Calling = Who->Fields.Find(TEXT("calling")))
			{
				if (!Calling->IsEmpty()) { About += TEXT(", ") + *Calling; }
			}
			if (const FString* Standing = Who->Fields.Find(TEXT("standing")))
			{
				if (!Standing->IsEmpty())
				{
					About += FString::Printf(TEXT(" (%d)"),
						FMath::RoundToInt(FCString::Atof(**Standing)));
				}
			}
		}
	}
	if (About.IsEmpty())
	{
		About = FString::Printf(TEXT("%d, %d"), Targets[0].X, Targets[0].Y);
	}
	Head->SetText(FText::FromString(About));

	// WHERE THE CURSOR WAS -- AND ALWAYS FULLY ON SCREEN.
	//
	// Two things, and the second is the one that bites. A menu opened at the
	// cursor near the right edge runs off it, and a menu with its last two
	// lines past the bottom is a menu whose last two options do not exist. So
	// it is clamped into the viewport, which for a list opened near the bottom
	// means opening UPWARDS from the cursor -- the same thing every window of
	// this shape does and nobody notices until it is missing.
	//
	// And when there is no cursor at all -- the mouse outside the viewport,
	// which is every screenshot taken in this session -- it goes to the middle
	// rather than to the origin, where it sat invisible behind the panel and
	// looked like a menu that was not being drawn.
	if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Plate->Slot))
	{
		const float Scale = FMath::Max(UWidgetLayoutLibrary::GetViewportScale(this), 0.01f);
		FVector2D View = UWidgetLayoutLibrary::GetViewportSize(this) / Scale;
		FVector2D Where = View * 0.5f;
		if (APlayerController* PC = GetOwningPlayer())
		{
			float MX = 0.f, MY = 0.f;
			if (PC->GetMousePosition(MX, MY))
			{
				Where = FVector2D(MX / Scale, MY / Scale);
			}
		}
		// The plate has not been laid out yet, so its size is estimated from
		// what is in it: a row is about eighteen high and the widest label
		// decides the width. An estimate is enough -- being a few pixels out
		// is invisible, being off the edge is not.
		float Widest = 0.f;
		for (UWidget* Child : Rows->GetAllChildren())
		{
			if (const UIntervalMenuRow* Row = Cast<UIntervalMenuRow>(Child))
			{
				Widest = FMath::Max(Widest, 8.f * Row->Label.Len());
			}
		}
		const FVector2D Size(FMath::Max(Widest + 28.f, 120.f), Lines * 19.f + 26.f);
		Where.X = FMath::Clamp(Where.X, 4.f, FMath::Max(View.X - Size.X - 4.f, 4.f));
		Where.Y = FMath::Clamp(Where.Y, 4.f, FMath::Max(View.Y - Size.Y - 4.f, 4.f));
		Slot->SetPosition(Where);
	}
	Plate->SetVisibility(ESlateVisibility::Visible);
}
