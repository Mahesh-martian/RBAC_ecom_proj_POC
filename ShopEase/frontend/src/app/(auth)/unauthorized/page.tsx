import Image from "next/image";
import Link from "next/link";
import React from "react";

const Unauthorized = () => {
  return (
    <div className="relative h-screen w-screen flex items-center justify-center bg-[#fed801]">
      <Image
        src="/images/unauthorized.jpg"
        alt="Unauthorized"
        height={500}
        width={800}
        className="absolute object-cover "
      />
      <div className="relative z-10 text-center">
        <Link href="/">
          <span className="bg-blue-500 text-white rounded-lg py-3 px-5 text-lg font-semibold">
            Back to Home
          </span>
        </Link>
      </div>
    </div>
  );
};

export default Unauthorized;
