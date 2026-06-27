import SignUpForm from "@/components/forms/SignUpForm";
import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import { H2, Paragraph } from "@/components/shared/CustomTypography";
import Image from "next/image";
import React from "react";
import { IoBriefcaseOutline } from "react-icons/io5";

const SignUp = () => {
  return (
    <div className="">
      <CustomBreadcrumb
        items={[{ label: "Home", path: "/" }, { label: "Sign Up" }]}
        title="Sign Up"
      />
      <div className="flex justify-center items-center py-20">
        <div className="max-w-3xl  bg-card text-card-foreground rounded-2xl w-full shadow-lg dark:shadow-[0_30px_75px_rgba(255,255,255,0.2)]">
          <Image
            src="/images/sign-up.jpg"
            alt="Signup"
            height={200}
            width={300}
            className="object-cover rounded-t-2xl w-full max-h-52"
          />
          <div className="px-16 pb-16">
            <div className="w-full pt-16">
              <div className="flex justify-start items-start gap-5">
                <div className="bg-muted p-3 rounded-lg">
                  <IoBriefcaseOutline className="text-3xl text-primary font-bold " />
                </div>
                <div>
                  <H2 className="font-bold text-foreground dark:text-primary-background">
                    Sign Up
                  </H2>
                  <Paragraph className="text-sm lg:text-lg pt-5 text-muted-foreground">
                    Your personal data will be used to support your experience
                    throughout this website, to manage access to your account.
                  </Paragraph>
                </div>
              </div>
            </div>
            <div className="pt-8">
              <SignUpForm />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignUp;
