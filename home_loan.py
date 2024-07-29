import pandas as pd
import matplotlib.pyplot as plt


class HomeLoan:

    @staticmethod
    def get_recurring_payment_c(*, n, p, r):
        return p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    @staticmethod
    def get_current_rate_r(*, k, r, Rs: pd.DataFrame | None, month):
        if Rs is not None:
            rel_Rs = Rs[month >= Rs["month"]]["rate"]
            if len(rel_Rs) > 0:
                R = rel_Rs.iloc[-1]
                r = R / k
        return r

    @staticmethod
    def get_accumulated_offset_o(*, Os: pd.DataFrame | None, month):
        o = 0
        if Os is not None:
            rel_Os = Os[month >= Os["month"]]["amount"]
            if len(rel_Os) > 0:
                o = rel_Os.sum()
        return o

    def __init__(self, *, N, k, P, R0):
        self.N = N
        self.k = k
        self.P = P
        self.R0 = R0

        self.n = self.N * self.k
        self.r0 = self.R0 / self.k
        self.c0 = self.get_recurring_payment_c(n=self.n, p=self.P, r=self.r0)
        self.m0 = self.c0 * self.k / 12

    def print(self):
        print("--- Configuration ---")
        print("Term length N:", self.N, "yrs")
        print("Payments per year k:", self.k)
        print("Principal P:", self.P)
        print("Initial interest R0:", self.R0 * 100, "% pa")
        print("")
        print("--- Analysis ---")
        print("Initial payment per month m0:", f"{self.m0:.2f}")
        print("Initial total amount to be paid:", f"{(self.n * self.c0):.2f}")
        print(
            "Initial total interest to be paid: ",
            f"{(self.n * self.c0 - self.P):.2f}",
            f"({((self.n * self.c0 - self.P) / (self.n * self.c0) * 100):.2f}",
            "%)",
        )
        print("")

    def simulate(self, *, Rs=None, Os=None):
        plan = []

        p = self.P
        r = self.r0
        o = 0
        e = 0
        i = 0
        while p > o + e:
            i += 1

            prev_month = (i - 1) * 12 / self.k
            curr_month = (i + 0) * 12 / self.k
            curr_year = (i + 0) / self.k

            r = self.get_current_rate_r(r=r, k=self.k, Rs=Rs, month=prev_month)
            c = self.get_recurring_payment_c(n=self.n - i, p=p, r=r)

            prev_o = self.get_accumulated_offset_o(Os=Os, month=prev_month)
            o = self.get_accumulated_offset_o(Os=Os, month=curr_month)
            o_pay = o - prev_o

            total_pay = c

            interest_pay_planned = p * r
            principal_pay = total_pay - interest_pay_planned

            interest_pay = (p - (o + e)) * r
            extra_pay = interest_pay_planned - interest_pay

            p -= principal_pay
            e += extra_pay

            plan.append(
                (
                    i,
                    curr_month,
                    curr_year,
                    r * self.k,
                    o_pay,
                    interest_pay,
                    principal_pay,
                    extra_pay,
                    p,
                    o,
                    e,
                )
            )

        plan = pd.DataFrame(
            plan,
            columns=[
                "i",
                "month",
                "year",
                "rate",
                "offset_pay",
                "interest_pay",
                "principal_pay",
                "extra_pay",
                "principal",
                "offset",
                "extra",
            ],
        )
        plan.set_index("i", drop=False, inplace=True)

        print("--- Simulation ---")
        print("  - HEAD -")
        print(plan.head(5))
        print("  - TAIL -")
        print(plan.tail(5))

        return plan


def plot(ax1, plan: pd.DataFrame):
    ax2 = ax1.twinx()
    # axis 1

    ax1.plot(plan["year"], plan["principal"], "k-", label="principal")
    ax1.plot(plan["year"], plan["offset"], "m-", label="offset")
    ax1.plot(plan["year"], plan["offset"] + plan["extra"], "c-", label="offset + extra")

    principal_half = plan.loc[
        plan["principal"] <= 0.5 * plan["principal"].iloc[0]
    ].iloc[0]
    ax1.axhline(y=principal_half["principal"], color="y", linestyle="-")
    ax1.axvline(x=principal_half["year"], color="y", linestyle="-")

    ax1.set_xlabel("Years")
    ax1.set_ylabel("Remaining")
    ax1.legend(loc="lower left")

    # axis 2

    ax2.plot(plan["year"], plan["interest_pay"], "r--", label="interest")
    ax2.plot(plan["year"], plan["principal_pay"], "g--", label="principal")
    ax2.plot(
        plan["year"],
        plan["interest_pay"] + plan["principal_pay"] + plan["extra_pay"],
        "b--",
        label="interest + principal + exta",
    )

    interest_principal_turnover = plan.loc[
        plan["principal_pay"] >= plan["interest_pay"]
    ].iloc[0]
    ax2.axhline(
        y=interest_principal_turnover["principal_pay"], color="y", linestyle="--"
    )
    ax2.axvline(x=interest_principal_turnover["year"], color="y", linestyle="--")

    ax2.set_ylabel("Payments")
    ax2.legend(loc="center right")


if __name__ == "__main__":

    # setup

    P = 1100000
    N = 20
    k = 12
    R0 = 0.065

    Rs = []
    # Rs.append((24, 0.085))
    # Rs.append((48, 0.065))
    Rs = pd.DataFrame(Rs, columns=["month", "rate"])
    Rs.set_index("month", drop=False, inplace=True)

    Os = []
    Os.append((0, 100000))
    Os = pd.DataFrame(Os, columns=["month", "amount"])
    Os.set_index("month", drop=False, inplace=True)

    # loan 1

    myLoan1 = HomeLoan(N=N, k=k, P=P, R0=R0)
    myLoan1.print()
    plan1 = myLoan1.simulate()

    # loan2

    myLoan2 = HomeLoan(N=N, k=k, P=P, R0=R0)
    myLoan2.print()
    plan2 = myLoan2.simulate(Rs=Rs, Os=Os)

    # plot

    _, axs = plt.subplots(nrows=2, figsize=(15, 15))

    plot(axs[0], plan1)
    plot(axs[1], plan2)

    axs[1].set_xlim(axs[0].get_xlim())

    plt.show()
